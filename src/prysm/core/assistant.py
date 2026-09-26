import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prysm.brain.context import ContextManager
    from prysm.tools.executor import ToolExecutor

from prysm.brain.provider import LLMProvider
from prysm.core.events import (
    AssistantThinkingCompleted,
    AssistantThinkingStarted,
    ErrorOccurred,
    EventBus,
    InputReceived,
    ProcessingCompleted,
    ProcessingStarted,
    ResponseGenerated,
    StateChanged,
)
from prysm.core.exceptions import InvalidStateTransitionError
from prysm.core.lifecycle import Lifecycle
from prysm.core.state import AssistantState
from prysm.models.interactions import BrainResponse, UserInput
from prysm.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 8

# Valid state transitions
_TRANSITIONS: dict[AssistantState, set[AssistantState]] = {
    AssistantState.STARTING: {AssistantState.IDLE, AssistantState.ERROR},
    AssistantState.IDLE: {
        AssistantState.LISTENING,
        AssistantState.PROCESSING,
        AssistantState.STOPPING,
        AssistantState.ERROR,
    },
    AssistantState.LISTENING: {
        AssistantState.PROCESSING,
        AssistantState.IDLE,
        AssistantState.ERROR,
    },
    AssistantState.PROCESSING: {
        AssistantState.THINKING,
        AssistantState.IDLE,
        AssistantState.ERROR,
    },
    AssistantState.THINKING: {
        AssistantState.EXECUTING_TOOL,
        AssistantState.RESPONDING,
        AssistantState.ERROR,
    },
    AssistantState.EXECUTING_TOOL: {
        AssistantState.THINKING,
        AssistantState.ERROR,
    },
    AssistantState.RESPONDING: {
        AssistantState.SPEAKING,
        AssistantState.IDLE,
        AssistantState.ERROR,
    },
    AssistantState.SPEAKING: {
        AssistantState.IDLE,
        AssistantState.ERROR,
    },
    AssistantState.ERROR: {AssistantState.IDLE, AssistantState.STOPPING},
    AssistantState.STOPPING: {AssistantState.STOPPED},
    AssistantState.STOPPED: set(),
}


class PrysmAssistant:
    """Core assistant — orchestrates the full request/response pipeline."""

    def __init__(
        self,
        event_bus: EventBus,
        tool_registry: ToolRegistry,
        llm_provider: LLMProvider,
        context_manager: "ContextManager",
        tool_executor: "ToolExecutor",
    ) -> None:
        self.event_bus = event_bus
        self.tool_registry = tool_registry
        self.llm_provider = llm_provider
        self.context_manager = context_manager
        self.tool_executor = tool_executor

        self.state = AssistantState.STARTING
        self.lifecycle = Lifecycle()
        self.lifecycle.on_startup(self._initialize)
        self.lifecycle.on_shutdown(self._cleanup)

        self._stop_event: asyncio.Event = asyncio.Event()
        self._background_tasks: set[asyncio.Task] = set()

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    async def set_state(self, new_state: AssistantState, reason: str | None = None) -> None:
        if self.state == new_state:
            return

        allowed = _TRANSITIONS.get(self.state, set())
        if new_state not in allowed and new_state != AssistantState.ERROR:
            msg = f"Invalid transition {self.state.name} -> {new_state.name}"
            logger.warning(msg)
            raise InvalidStateTransitionError(msg)

        old_state = self.state
        self.state = new_state
        logger.debug(f"State: {old_state.name} -> {new_state.name}" + (f" ({reason})" if reason else ""))

        await self.event_bus.publish(
            StateChanged(previous_state=old_state, new_state=new_state, reason=reason)
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def _initialize(self) -> None:
        logger.info("PrysmAssistant initializing...")
        await self.set_state(AssistantState.IDLE, reason="startup complete")

    async def _cleanup(self) -> None:
        logger.info("PrysmAssistant shutting down...")
        if self.state not in (AssistantState.STOPPING, AssistantState.STOPPED):
            await self.set_state(AssistantState.STOPPING, reason="shutdown requested")

        for task in self._background_tasks:
            task.cancel()
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            self._background_tasks.clear()

        await self.set_state(AssistantState.STOPPED, reason="cleanup complete")

    async def run(self) -> None:
        """Start the assistant and block until stopped."""
        await self.lifecycle.start()
        try:
            await self._stop_event.wait()
        except asyncio.CancelledError:
            pass
        finally:
            await self.lifecycle.stop()

    async def stop(self) -> None:
        self._stop_event.set()

    # ------------------------------------------------------------------
    # Core pipeline
    # ------------------------------------------------------------------

    async def process(self, user_input: UserInput) -> BrainResponse | None:
        """Process a user input through the full LLM + tool-execution pipeline."""
        if self.state != AssistantState.IDLE:
            logger.warning(f"Cannot process — assistant is {self.state.name}")
            return None

        try:
            await self.event_bus.publish(InputReceived(input_text=user_input.text, source=user_input.source))
            await self.set_state(AssistantState.PROCESSING, reason="input received")

            self.context_manager.add_user_message(user_input.text)

            iteration = 0
            final_response: BrainResponse | None = None

            while iteration < MAX_TOOL_ITERATIONS:
                iteration += 1

                await self.set_state(AssistantState.THINKING, reason="calling LLM")
                if iteration == 1:
                    await self.event_bus.publish(ProcessingStarted())
                    await self.event_bus.publish(AssistantThinkingStarted())

                messages = self.context_manager.get_messages()
                tools = self._build_tool_schemas()

                response = await self.llm_provider.generate_response(
                    messages, tools or None
                )

                self.context_manager.add_assistant_message(
                    text=response.text, tool_calls=response.tool_calls
                )

                if response.tool_calls:
                    await self.set_state(AssistantState.EXECUTING_TOOL, reason="running tools")
                    results = await asyncio.gather(
                        *[self.tool_executor.execute(tc) for tc in response.tool_calls]
                    )
                    for result in results:
                        self.context_manager.add_tool_result(result)
                else:
                    final_response = response
                    break

            if iteration >= MAX_TOOL_ITERATIONS:
                logger.warning("Max tool iterations reached")

            if final_response and final_response.text:
                await self.event_bus.publish(AssistantThinkingCompleted())
                await self.set_state(AssistantState.RESPONDING, reason="final response ready")
                await self.event_bus.publish(ResponseGenerated(response_text=final_response.text))

            await self.event_bus.publish(ProcessingCompleted())
            await self.set_state(AssistantState.IDLE, reason="processing complete")
            return final_response

        except asyncio.CancelledError:
            await self.set_state(AssistantState.IDLE, reason="cancelled")
            raise
        except Exception as e:
            logger.exception("Error in processing pipeline")
            await self.event_bus.publish(ErrorOccurred(error_message=str(e), exception=e))
            await self.set_state(AssistantState.ERROR, reason=str(e))
            await self.set_state(AssistantState.IDLE, reason="recovered")
            return None

    def _build_tool_schemas(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": s["name"],
                    "description": s["description"],
                    "parameters": s["parameters"],
                },
            }
            for s in self.tool_registry.get_all_schemas()
        ]
