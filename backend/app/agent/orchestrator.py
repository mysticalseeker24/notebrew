"""Agent orchestrator — custom tool-calling loop with no framework dependency."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable, Optional

import openai

from app.config import settings
from app.llm_client import get_client
from app.models import (
    AgentState,
    ProcessingStatus,
    ToolCall,
)
from app.agent.tool_registry import ToolRegistry
from app.agent.prompts.system import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Custom AI agent that uses tool-calling to convert papers into notebooks.

    The orchestrator runs a loop:
      1. Send conversation history + tool definitions to the LLM.
      2. If the LLM responds with tool calls → execute them, append results,
         loop back to step 1.
      3. If the LLM responds with a final text message → return.
      4. Guard against infinite loops with max_iterations.
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        model: Optional[str] = None,
        on_progress: Optional[
            Callable[[str, float, str, Optional[str], Optional[str]], None]
        ] = None,
    ) -> None:
        self.registry = tool_registry
        self.model = model or settings.ORCHESTRATION_MODEL
        self.on_progress = on_progress
        self.max_iterations = settings.AGENT_MAX_ITERATIONS
        self.max_retries = settings.AGENT_MAX_RETRIES
        self.max_llm_calls = settings.MAX_LLM_CALLS_PER_TASK
        self.max_generate_code_calls = settings.MAX_GENERATE_CODE_CALLS
        self.max_runtime_seconds = settings.MAX_RUNTIME_SECONDS
        self.max_retry_per_tool = settings.MAX_RETRY_PER_TOOL
        self.client = get_client()

    def _get_model_name(self) -> str:
        """Resolve short model name to full OpenRouter model path."""
        mapping = {
            "gemini-3-flash-preview": settings.GEMINI_3_FLASH_MODEL,
            "minimax-m2.5": settings.MINIMAX_M25_MODEL,
        }
        return mapping.get(self.model, self.model)

    @staticmethod
    def _status_for_tool(tool_name: str) -> str:
        """Map tool names to processing status values used by the status API."""
        mapping = {
            "parse_pdf": ProcessingStatus.PARSING_PDF.value,
            "parse_arxiv": ProcessingStatus.PARSING_PDF.value,
            "plan_notebook": ProcessingStatus.PLANNING.value,
            "generate_code": ProcessingStatus.GENERATING_CODE.value,
            "validate_code": ProcessingStatus.VALIDATING_CODE.value,
            "assemble_notebook": ProcessingStatus.ASSEMBLING_NOTEBOOK.value,
        }
        return mapping.get(tool_name, ProcessingStatus.PLANNING.value)

    def _emit_progress(
        self,
        status: str,
        progress: float,
        message: str,
        current_tool: Optional[str] = None,
        current_section: Optional[str] = None,
    ) -> None:
        """Emit a progress update if a callback is registered."""
        if self.on_progress:
            self.on_progress(status, progress, message, current_tool, current_section)

    async def run(self, task_description: str, state: AgentState) -> AgentState:
        """Run the agent loop until completion or max iterations."""
        started_at = time.monotonic()
        llm_calls = 0
        generate_code_calls = 0

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task_description},
        ]

        tool_definitions = self.registry.get_tool_definitions()
        state.status = ProcessingStatus.PLANNING

        for iteration in range(1, self.max_iterations + 1):
            state.iteration = iteration
            logger.info("Agent iteration %d/%d", iteration, self.max_iterations)
            self._emit_progress(
                state.status.value,
                min(10 + (iteration / self.max_iterations) * 80, 90),
                f"Agent thinking (step {iteration})...",
                current_tool=None,
            )

            elapsed = time.monotonic() - started_at
            if elapsed > self.max_runtime_seconds:
                state.status = ProcessingStatus.FAILED
                state.error = f"Task exceeded runtime budget ({self.max_runtime_seconds}s)."
                self._emit_progress(state.status.value, 0, state.error, current_tool=None)
                return state

            if llm_calls >= self.max_llm_calls:
                state.status = ProcessingStatus.FAILED
                state.error = f"Task exceeded LLM call budget ({self.max_llm_calls})."
                self._emit_progress(state.status.value, 0, state.error, current_tool=None)
                return state

            try:
                llm_calls += 1
                response = await self._call_llm(messages, tool_definitions)
            except Exception as exc:
                logger.exception("LLM call failed on iteration %d", iteration)
                state.status = ProcessingStatus.FAILED
                state.error = f"LLM call failed: {exc}"
                return state

            choice = response.choices[0]
            assistant_msg = choice.message

            # ----- Case 1: LLM wants to call tools -----
            if assistant_msg.tool_calls:
                messages.append(self._assistant_msg_to_dict(assistant_msg))

                tool_calls_info = []
                for tc in assistant_msg.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        args = {}

                    tool_calls_info.append(
                        {
                            "name": tc.function.name,
                            "arguments": args,
                            "tool_call_id": tc.id,
                        }
                    )

                logger.info(
                    "Executing %d tool(s): %s",
                    len(tool_calls_info),
                    [c["name"] for c in tool_calls_info],
                )

                generate_code_calls += sum(
                    1 for call in tool_calls_info if call["name"] == "generate_code"
                )
                if generate_code_calls > self.max_generate_code_calls:
                    state.status = ProcessingStatus.FAILED
                    state.error = (
                        "Task exceeded generate_code call budget "
                        f"({self.max_generate_code_calls})."
                    )
                    self._emit_progress(state.status.value, 0, state.error, current_tool="generate_code")
                    return state

                tool_names = ", ".join(c["name"] for c in tool_calls_info)
                self._emit_progress(
                    self._status_for_tool(tool_calls_info[0]["name"]) if tool_calls_info else state.status.value,
                    min(10 + (iteration / self.max_iterations) * 80, 90),
                    f"Running tools: {tool_names}",
                    current_tool=tool_calls_info[0]["name"] if tool_calls_info else None,
                )

                results = await self._execute_tool_calls_with_retries(tool_calls_info)

                for result in results:
                    result_content = (
                        json.dumps(result.result, default=str)
                        if result.success
                        else json.dumps({"error": result.error})
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": result.tool_call_id,
                            "content": result_content,
                        }
                    )
                    self._update_state_from_tool(state, result)

                failed_tools = [r for r in results if not r.success]
                if failed_tools:
                    first_error = failed_tools[0]
                    state.status = ProcessingStatus.FAILED
                    state.error = (
                        f"Tool '{first_error.name}' failed after retries: {first_error.error}"
                    )
                    self._emit_progress(state.status.value, 0, state.error, current_tool=first_error.name)
                    return state

                ran_plan = any(r.success and r.name == "plan_notebook" for r in results)
                ran_generate = any(r.success and r.name == "generate_code" for r in results)
                if ran_plan and not ran_generate:
                    fanout_ok = await self._run_deterministic_generation_pipeline(state)
                    if fanout_ok:
                        state.status = ProcessingStatus.COMPLETED
                        self._emit_progress(
                            ProcessingStatus.COMPLETED.value,
                            100,
                            "Notebook generation complete",
                            current_tool="assemble_notebook",
                        )
                        return state
                    if state.error:
                        state.status = ProcessingStatus.FAILED
                        self._emit_progress(state.status.value, 0, state.error, current_tool="generate_code")
                        return state

                continue

            # ----- Case 2: Final text response -----
            if choice.finish_reason == "stop" and assistant_msg.content:
                logger.info("Agent completed with final message")
                if state.status != ProcessingStatus.FAILED:
                    state.status = ProcessingStatus.COMPLETED
                self._emit_progress(
                    state.status.value,
                    100,
                    "Notebook generation complete",
                    current_tool="assemble_notebook",
                )
                return state

            # ----- Case 3: Truncated response (finish_reason=length) -----
            if choice.finish_reason == "length":
                logger.warning("Response truncated, asking to continue")
                messages.append(self._assistant_msg_to_dict(assistant_msg))
                messages.append({
                    "role": "user",
                    "content": (
                        "Your response was truncated. Please continue with shorter "
                        "tool calls. Call one tool at a time with concise arguments."
                    ),
                })
                continue

            # ----- Case 4: Unexpected response -----
            logger.warning(
                "Unexpected finish_reason=%s, content=%s",
                choice.finish_reason,
                bool(assistant_msg.content),
            )
            messages.append(self._assistant_msg_to_dict(assistant_msg))

        # Max iterations reached
        logger.warning("Agent reached max iterations (%d)", self.max_iterations)
        if state.notebook_path:
            state.status = ProcessingStatus.COMPLETED
            self._emit_progress(
                state.status.value,
                100,
                "Notebook generated (max iterations reached)",
                current_tool="assemble_notebook",
            )
        else:
            state.status = ProcessingStatus.FAILED
            state.error = "Agent exceeded maximum iterations without completing"
            self._emit_progress(state.status.value, 0, state.error, current_tool=None)

        return state

    async def _execute_tool_calls_with_retries(
        self,
        calls: list[dict[str, Any]],
    ) -> list[Any]:
        """Execute tool calls with bounded retry attempts per tool."""
        pending = list(calls)
        attempts: dict[str, int] = {call["tool_call_id"]: 0 for call in calls}
        completed: dict[str, Any] = {}

        while pending:
            results = await self.registry.execute_parallel(pending)
            next_pending: list[dict[str, Any]] = []

            for call, result in zip(pending, results):
                call_id = call["tool_call_id"]
                if result.success:
                    completed[call_id] = result
                    continue

                attempts[call_id] += 1
                if attempts[call_id] <= self.max_retry_per_tool:
                    logger.warning(
                        "Retrying tool %s (%d/%d) due to error: %s",
                        call["name"],
                        attempts[call_id],
                        self.max_retry_per_tool,
                        result.error,
                    )
                    next_pending.append(call)
                else:
                    completed[call_id] = result

            pending = next_pending

        return [completed[call["tool_call_id"]] for call in calls if call["tool_call_id"] in completed]

    async def _call_llm(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> Any:
        """Make a single LLM API call with retry + fallback logic."""
        model_name = self._get_model_name()

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=tools if tools else openai.NOT_GIVEN,
                    temperature=0.3,
                    max_tokens=16384,
                )
                return response
            except Exception as exc:
                logger.warning(
                    "LLM call attempt %d/%d failed: %s",
                    attempt,
                    self.max_retries,
                    exc,
                )
                if attempt == self.max_retries:
                    fallback = self._get_fallback_model_name()
                    if model_name != fallback:
                        logger.info("Switching to fallback model: %s", fallback)
                        model_name = fallback
                        continue
                    raise

        raise RuntimeError("All LLM call attempts exhausted")

    def _get_fallback_model_name(self) -> str:
        """Get the fallback model's full OpenRouter path."""
        mapping = {
            "gemini-3-flash-preview": settings.GEMINI_3_FLASH_MODEL,
            "minimax-m2.5": settings.MINIMAX_M25_MODEL,
        }
        return mapping.get(settings.FALLBACK_MODEL, settings.MINIMAX_M25_MODEL)

    @staticmethod
    def _assistant_msg_to_dict(msg: Any) -> dict[str, Any]:
        """Convert an OpenAI assistant message object to a serializable dict."""
        d: dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            d["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        return d

    def _update_state_from_tool(self, state: AgentState, result: Any) -> None:
        """Update the agent state based on a tool execution result."""
        if not result.success:
            return

        tool_name = result.name
        data = result.result

        if tool_name in ("parse_pdf", "parse_arxiv") and isinstance(data, dict):
            from app.models import PaperStructure
            state.paper_structure = PaperStructure(**data)
            state.status = ProcessingStatus.PLANNING

        elif tool_name == "plan_notebook" and isinstance(data, dict):
            from app.models import NotebookPlan
            state.notebook_plan = NotebookPlan(**data)
            state.status = ProcessingStatus.GENERATING_CODE

        elif tool_name == "generate_code" and isinstance(data, dict):
            state.generated_cells.append(data)
            state.status = ProcessingStatus.GENERATING_CODE

        elif tool_name == "validate_code":
            state.status = ProcessingStatus.VALIDATING_CODE

        elif tool_name == "assemble_notebook" and isinstance(data, dict):
            state.notebook_path = data.get("notebook_path")
            state.status = ProcessingStatus.ASSEMBLING_NOTEBOOK

    async def _run_deterministic_generation_pipeline(self, state: AgentState) -> bool:
        """Generate planned cells in parallel and assemble notebook deterministically."""
        if not state.notebook_plan:
            state.error = "Notebook plan unavailable for deterministic generation."
            return False

        if not state.paper_structure:
            state.error = "Paper structure unavailable for deterministic generation."
            return False

        plan = state.notebook_plan
        paper = state.paper_structure
        section_map = {
            sec.title: sec for sec in paper.sections
        }

        calls: list[dict[str, Any]] = []
        prebuilt_cells: dict[int, dict[str, Any]] = {}
        for idx, cell in enumerate(plan.cells):
            section = section_map.get(cell.section_ref or "")
            if str(cell.cell_type).lower() == "markdown":
                prebuilt_cells[idx] = self._build_fast_markdown_cell(
                    purpose=cell.purpose,
                    section_title=cell.section_ref or "",
                    section_content=(section.content if section else ""),
                    equations=(section.equations if section else paper.equations[:3]),
                )
                continue

            calls.append(
                {
                    "name": "generate_code",
                    "tool_call_id": f"fanout-generate-{idx}",
                    "arguments": {
                        "cell_type": cell.cell_type,
                        "cell_purpose": cell.purpose,
                        "paper_title": paper.metadata.title,
                        "section_title": cell.section_ref or "",
                        "section_content": (section.content if section else ""),
                        "equations": (section.equations if section else paper.equations[:4]),
                        "previous_code_context": "Fast mode: concise runnable code only.",
                    },
                }
            )

        if not calls and not prebuilt_cells:
            state.error = "Notebook plan has no cells to generate."
            return False

        self._emit_progress(
            ProcessingStatus.GENERATING_CODE.value,
            75,
            f"Generating {len(calls)} code cells in parallel...",
            current_tool="generate_code",
        )
        generated = await self._execute_tool_calls_with_retries(calls) if calls else []

        failed = [r for r in generated if not r.success]
        if failed:
            state.error = f"Parallel generation failed for '{failed[0].name}': {failed[0].error}"
            return False

        generated_by_index: dict[int, dict[str, Any]] = dict(prebuilt_cells)
        dependency_set: set[str] = set(plan.dependencies)
        for result in generated:
            idx = int(str(result.tool_call_id).split("-")[-1])
            payload = result.result if isinstance(result.result, dict) else {}
            generated_by_index[idx] = payload
            for dep in payload.get("dependencies", []) or []:
                if isinstance(dep, str) and dep.strip():
                    dependency_set.add(dep.strip())

        ordered_cells = [generated_by_index[i] for i in sorted(generated_by_index.keys())]
        state.generated_cells = ordered_cells

        # Validate generated code cells before notebook assembly.
        code_validate_calls: list[dict[str, Any]] = []
        for idx, cell in enumerate(ordered_cells):
            if str(cell.get("cell_type", "")).lower() != "code":
                continue
            code_validate_calls.append(
                {
                    "name": "validate_code",
                    "tool_call_id": f"fanout-validate-{idx}",
                    "arguments": {
                        "code": cell.get("content", ""),
                        "cell_index": idx,
                    },
                }
            )

        if code_validate_calls:
            self._emit_progress(
                ProcessingStatus.VALIDATING_CODE.value,
                85,
                "Validating generated code cells...",
                current_tool="validate_code",
            )
            validations = await self._execute_tool_calls_with_retries(code_validate_calls)
            invalid = [
                r for r in validations
                if not r.success or not bool((r.result or {}).get("is_valid", False))
            ]
            if invalid:
                first = invalid[0]
                state.error = (
                    f"Generated code validation failed for {first.tool_call_id}: "
                    f"{first.error or (first.result or {}).get('errors', ['unknown'])[0]}"
                )
                return False

        assemble_call = {
            "name": "assemble_notebook",
            "tool_call_id": "fanout-assemble",
            "arguments": {
                "title": plan.title,
                "authors": paper.metadata.authors,
                "cells": ordered_cells,
                "dependencies": sorted(dependency_set),
            },
        }

        self._emit_progress(
            ProcessingStatus.ASSEMBLING_NOTEBOOK.value,
            95,
            "Assembling notebook artifact...",
            current_tool="assemble_notebook",
        )
        assembled = await self.registry.execute(
            tool_name=assemble_call["name"],
            arguments=assemble_call["arguments"],
            tool_call_id=assemble_call["tool_call_id"],
        )

        if not assembled.success:
            state.error = f"Failed to assemble notebook: {assembled.error}"
            return False

        self._update_state_from_tool(state, assembled)
        return bool(state.notebook_path)

    @staticmethod
    def _build_fast_markdown_cell(
        purpose: str,
        section_title: str,
        section_content: str,
        equations: list[str],
    ) -> dict[str, Any]:
        """Create concise markdown locally to avoid extra LLM latency."""
        title = section_title.strip() or "Explanation"
        summary = (section_content or "").strip().replace("\n", " ")
        summary = " ".join(summary.split())
        if len(summary) > 420:
            summary = summary[:420].rstrip() + "..."

        lines = [
            f"## {title}",
            "",
            f"**Goal:** {purpose}",
            "",
            summary or "Key ideas from this section are summarized for quick understanding.",
        ]

        if equations:
            lines.extend([
                "",
                "**Key equation:**",
                f"$${equations[0]}$$",
            ])

        lines.extend([
            "",
            "**What to observe:** Focus on how this section connects to the runnable cells below.",
        ])

        return {
            "cell_type": "markdown",
            "content": "\n".join(lines),
            "purpose": purpose,
            "section_ref": section_title,
            "dependencies": [],
        }
