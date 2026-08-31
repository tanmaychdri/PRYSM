from prysm.brain.mock import MockLLMProvider
from prysm.brain.provider import LLMProvider
from prysm.config.settings import Settings
from prysm.core.assistant import PrysmAssistant
from prysm.core.events import EventBus
from prysm.tools.registry import ToolRegistry


class ApplicationContainer:
    """Central Dependency Injection container."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.event_bus = EventBus()
        self.tool_registry = ToolRegistry()
        self.llm_provider: LLMProvider = MockLLMProvider()

        self.assistant = PrysmAssistant(
            event_bus=self.event_bus,
            tool_registry=self.tool_registry,
            llm_provider=self.llm_provider,
        )
