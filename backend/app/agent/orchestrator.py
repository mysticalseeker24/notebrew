"""Agent orchestrator — custom tool-calling loop with no framework dependency."""

from __future__ import annotations

import json
import logging
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
        self.model = model or settings.PRIMARY_MODEL
        self.on_progress = on_progress
        self.max_iterations = settings.AGENT_MAX_ITERATIONS
        self.max_retries = settings.AGENT_MAX_RETRIES
        self.client = get_client()

    def _get_model_name(self) -> str:
        """Resolve short model name to full OpenRouter model path."""
        mapping = {
            "gemini-3-flash-preview": settings.GEMINI_3_FLASH_MODEL,
            "minimax-m2.5": settings.MINIMAX_M25_MODEL,
        }
        return mapping.get(self.model, settings.GEMINI_3_FLASH_MODEL)

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

            try:
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

                tool_names = ", ".join(c["name"] for c in tool_calls_info)
                self._emit_progress(
                    self._status_for_tool(tool_calls_info[0]["name"]) if tool_calls_info else state.status.value,
                    min(10 + (iteration / self.max_iterations) * 80, 90),
                    f"Running tools: {tool_names}",
                    current_tool=tool_calls_info[0]["name"] if tool_calls_info else None,
                )

                results = await self.registry.execute_parallel(tool_calls_info)

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
