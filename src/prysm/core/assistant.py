import asyncio
import logging

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
from prysm.core.lifecycle import Lifecycle
from prysm.core.state import AssistantState
from prysm.models.interactions import BrainResponse, RequestContext, UserInput
from prysm.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class PrysmAssistant:
    """Core assistant orchestrating execution pipeline and state."""

    def __init__(
        self,
        event_bus: EventBus,
        tool_registry: ToolRegistry,
        llm_provider: LLMProvider,
        context_manager: "ContextManager",
        tool_executor: "ToolExecutor",
    ):
        self.event_bus = event_bus
        self.tool_registry = tool_registry
        self.llm_provider = llm_provider
        self.context_manager = context_manager
        self.tool_executor = tool_executor

        self.lifecycle = Lifecycle()
        self.state = AssistantState.STARTING

        self.lifecycle.on_startup(self._initialize)
        self.lifecycle.on_shutdown(self._cleanup)

        self._background_tasks: set[asyncio.Task[None]] = set()

        # Valid transition rules
        self._valid_transitions: dict[AssistantState, set[AssistantState]] = {
            AssistantState.STARTING: {AssistantState.IDLE, AssistantState.ERROR},
            AssistantState.IDLE: {
                AssistantState.LISTENING,
                AssistantState.PROCESSING,
                AssistantState.SPEAKING,
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
            AssistantState.ERROR: {AssistantState.STOPPING, AssistantState.IDLE},
            AssistantState.STOPPING: {AssistantState.STOPPED},
            AssistantState.STOPPED: set(),
        }

    async def set_state(
        self, new_state: AssistantState, reason: str | None = None
    ) -> None:
        """Change state and publish state change event if valid."""
        if self.state == new_state:
            return

        allowed = self._valid_transitions.get(self.state, set())
        if new_state not in allowed and new_state != AssistantState.ERROR:
            logger.warning(
                f"Invalid state transition attempted: {self.state.name} -> {new_state.name}"
            )
            raise RuntimeError(
                f"Invalid transition {self.state.name} -> {new_state.name}"
            )

        logger.info(f"State transition: {self.state.name} -> {new_state.name}")
        old_state = self.state
        self.state = new_state

        await self.event_bus.publish(
            StateChanged(previous_state=old_state, new_state=new_state, reason=reason)
        )

    async def _initialize(self) -> None:
        """Internal initialization logic."""
        logger.info("Initializing PrysmAssistant...")
        await self.set_state(AssistantState.IDLE, reason="Startup complete")

    async def _cleanup(self) -> None:
        """Internal cleanup logic."""
        logger.info("Cleaning up PrysmAssistant...")
        if self.state not in (AssistantState.STOPPING, AssistantState.STOPPED):
            await self.set_state(AssistantState.STOPPING, reason="Shutdown requested")

        for task in self._background_tasks:
            task.cancel()

        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            self._background_tasks.clear()

        if hasattr(self, "_stop_event"):
            self._stop_event.set()

        await self.set_state(AssistantState.STOPPED, reason="Cleanup complete")

    async def run(self) -> None:
        """Run the main assistant loop."""
        await self.lifecycle.start()
        try:
            self._stop_event = asyncio.Event()
            await self._stop_event.wait()
        except asyncio.CancelledError:
            pass
        finally:
            await self.lifecycle.stop()

    async def stop(self) -> None:
        """Public method to programmatically stop the assistant."""
        if hasattr(self, "_stop_event"):
            self._stop_event.set()
        else:
            await self.lifecycle.stop()

    async def process(self, user_input: UserInput) -> BrainResponse | None:
        """Process a user input through the core pipeline, including tool execution loops."""
        if self.state != AssistantState.IDLE:
            logger.warning("Assistant is not IDLE, cannot process input right now.")
            return None

        try:
            await self.event_bus.publish(
                InputReceived(input_text=user_input.text, source=user_input.source)
            )
            await self.set_state(AssistantState.PROCESSING, reason="Input received")
            
            # Add to context
            self.context_manager.add_user_message(user_input.text)

            MAX_TOOL_ITERATIONS = 8
            iteration = 0
            final_response = None
            
            while iteration < MAX_TOOL_ITERATIONS:
                iteration += 1
                
                await self.set_state(AssistantState.THINKING, reason="Calling Brain")
                if iteration == 1:
                    await self.event_bus.publish(ProcessingStarted())
                    await self.event_bus.publish(AssistantThinkingStarted())

                messages = self.context_manager.get_messages()
                
                # Format tools for provider
                tools = []
                for schema in self.tool_registry.get_all_schemas():
                    tools.append({
                        "type": "function",
                        "function": {
                            "name": schema["name"],
                            "description": schema["description"],
                            "parameters": schema["parameters"],
                        }
                    })

                response = await self.llm_provider.generate_response(messages, tools if tools else None)

                # Add assistant response to context
                self.context_manager.add_assistant_message(
                    text=response.text, tool_calls=response.tool_calls
                )

                if response.tool_calls:
                    await self.set_state(AssistantState.EXECUTING_TOOL, reason="Executing Tools")
                    # Execute all tools concurrently
                    tasks = []
                    for tool_call in response.tool_calls:
                        tasks.append(self.tool_executor.execute(tool_call))
                    
                    results = await asyncio.gather(*tasks)
                    
                    for result in results:
                        self.context_manager.add_tool_result(result)
                    
                    # If there's text along with tool calls, we can optionally broadcast it
                    if response.text:
                        await self.event_bus.publish(ResponseGenerated(response_text=response.text))
                        
                else:
                    final_response = response
                    break
            
            if iteration >= MAX_TOOL_ITERATIONS:
                logger.warning("Max tool iterations reached!")
                
            if final_response and final_response.text:
                await self.event_bus.publish(AssistantThinkingCompleted())
                await self.set_state(AssistantState.RESPONDING, reason="Final brain response")
                await self.event_bus.publish(ResponseGenerated(response_text=final_response.text))

            await self.event_bus.publish(ProcessingCompleted())
            await self.set_state(AssistantState.IDLE, reason="Processing complete")

            return final_response

        except asyncio.CancelledError:
            logger.info("Processing was cancelled.")
            await self.set_state(AssistantState.IDLE, reason="Cancelled")
            raise
        except Exception as e:
            logger.exception("Error during processing pipeline")
            await self.event_bus.publish(
                ErrorOccurred(error_message=str(e), exception=e)
            )
            await self.set_state(AssistantState.ERROR, reason=str(e))
            await self.set_state(AssistantState.IDLE, reason="Recovered from error")
            return None
