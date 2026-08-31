import logging

from prysm.core.events import EventBus
from prysm.core.lifecycle import Lifecycle
from prysm.core.state import AssistantState

logger = logging.getLogger(__name__)

class PrysmAssistant:
    """Core assistant class integrating event bus and state management."""
    def __init__(self):
        self.event_bus = EventBus()
        self.lifecycle = Lifecycle()
        self.state = AssistantState.STARTING
        
        self.lifecycle.on_startup(self._initialize)
        self.lifecycle.on_shutdown(self._cleanup)

    async def set_state(self, new_state: AssistantState) -> None:
        """Change state and publish state change event."""
        if self.state != new_state:
            logger.info(f"State transition: {self.state.name} -> {new_state.name}")
            self.state = new_state
            await self.event_bus.publish("state_changed", self.state)

    async def _initialize(self) -> None:
        """Internal initialization logic."""
        logger.info("Initializing PrysmAssistant...")
        await self.set_state(AssistantState.IDLE)

    async def _cleanup(self) -> None:
        """Internal cleanup logic."""
        logger.info("Cleaning up PrysmAssistant...")
        await self.set_state(AssistantState.STOPPING)
        if hasattr(self, "_stop_event"):
            self._stop_event.set()

    async def run(self) -> None:
        """Run the main assistant loop."""
        await self.lifecycle.start()
        try:
            import asyncio
            self._stop_event = asyncio.Event()
            await self._stop_event.wait()
        except asyncio.CancelledError:
            pass
        finally:
            await self.lifecycle.stop()
