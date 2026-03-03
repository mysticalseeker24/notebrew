"""Agent orchestrator — custom tool-calling loop with no framework dependency."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Optional

import openai

from app.config import settings
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
        on_progress: Optional[Callable[[str, float, str], None]] = None,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            tool_registry: Registry containing all available tools.
            model: Model identifier (e.g., 'gemini-3-flash-preview').
            on_progress: Callback ``(status, progress_pct, message)`` for
                real-time progress updates.
        """
        self.registry = tool_registry
        self.model = model or settings.PRIMARY_MODEL
        self.on_progress = on_progress
        self.max_iterations = settings.AGENT_MAX_ITERATIONS
        self.max_retries = settings.AGENT_MAX_RETRIES

        self.client = openai.AsyncOpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
        )

    def _get_model_name(self) -> str:
        """Resolve short model name to full OpenRouter model path."""
        mapping = {
            "gemini-3-flash-preview": settings.GEMINI_3_FLASH_MODEL,
            "minimax-m2.5": settings.MINIMAX_M25_MODEL,
        }
        return mapping.get(self.model, settings.GEMINI_3_FLASH_MODEL)

    def _emit_progress(self, status: str, progress: float, message: str) -> None:
        """Emit a progress update if a callback is registered."""
        if self.on_progress:
            self.on_progress(status, progress, message)

    async def run(self, task_description: str, state: AgentState) -> AgentState:
        """Run the agent loop until completion or max iterations.

        Args:
            task_description: The user-facing task (e.g., 'Convert this paper
                to a Jupyter notebook').
            state: Mutable agent state that accumulates results.

        Returns:
            Updated AgentState with the final result or error.
        """
        # Build initial messages
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task_description},
        ]

        tool_definitions = self.registry.get_tool_definitions()
        state.status = ProcessingStatus.PLANNING

        for iteration in range(1, self.max_iterations + 1):
            state.iteration = iteration
            logger.info(
                "Agent iteration %d/%d", iteration, self.max_iterations
            )
            self._emit_progress(
                state.status.value,
                min(10 + (iteration / self.max_iterations) * 80, 90),
                f"Agent thinking (step {iteration})...",
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
                # Append the assistant message (with tool_calls) to history
                messages.append(self._assistant_msg_to_dict(assistant_msg))

                # Execute all requested tool calls
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

                # Update progress with current tool names
                tool_names = ", ".join(c["name"] for c in tool_calls_info)
                self._emit_progress(
                    state.status.value,
                    min(10 + (iteration / self.max_iterations) * 80, 90),
                    f"Running tools: {tool_names}",
                )

                # Execute tools (concurrently if multiple)
                results = await self.registry.execute_parallel(tool_calls_info)

                # Append tool results to message history
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

                    # Update state based on tool results
                    self._update_state_from_tool(state, result)

                continue  # Loop back to ask LLM what to do next

            # ----- Case 2: LLM returns a final text response -----
            if choice.finish_reason == "stop" and assistant_msg.content:
                logger.info("Agent completed with final message")
                if state.status != ProcessingStatus.FAILED:
                    state.status = ProcessingStatus.COMPLETED
                self._emit_progress(
                    state.status.value, 100, "Notebook generation complete"
                )
                return state

            # ----- Case 3: Unexpected response -----
            logger.warning(
                "Unexpected finish_reason=%s, content=%s",
                choice.finish_reason,
                bool(assistant_msg.content),
            )
            messages.append(self._assistant_msg_to_dict(assistant_msg))

        # Max iterations reached
        logger.warning("Agent reached max iterations (%d)", self.max_iterations)
        if state.notebook_path:
            # We have a notebook even if we hit the limit
            state.status = ProcessingStatus.COMPLETED
            self._emit_progress(
                state.status.value, 100, "Notebook generated (max iterations reached)"
            )
        else:
            state.status = ProcessingStatus.FAILED
            state.error = "Agent exceeded maximum iterations without completing"
            self._emit_progress(state.status.value, 0, state.error)

        return state

    async def _call_llm(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> Any:
        """Make a single LLM API call with tool definitions.

        Includes retry logic with fallback to the secondary model.
        """
        model_name = self._get_model_name()

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=tools if tools else openai.NOT_GIVEN,
                    temperature=0.3,
                    max_tokens=4096,
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
                    # Try fallback model on final attempt
                    if model_name != self._get_fallback_model_name():
                        logger.info("Switching to fallback model")
                        model_name = self._get_fallback_model_name()
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

        if tool_name == "parse_pdf" and isinstance(data, dict):
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
