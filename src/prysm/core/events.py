import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Type, TypeVar

from prysm.core.state import AssistantState

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="BaseEvent")
Handler = Callable[[Any], Coroutine[Any, Any, None]]


@dataclass
class BaseEvent:
    pass


@dataclass
class StateChanged(BaseEvent):
    previous_state: AssistantState
    new_state: AssistantState
    reason: str | None = None


@dataclass
class InputReceived(BaseEvent):
    input_text: str
    source: str = "text"


@dataclass
class ProcessingStarted(BaseEvent):
    pass


@dataclass
class ProcessingCompleted(BaseEvent):
    pass


@dataclass
class AssistantThinkingStarted(BaseEvent):
    pass


@dataclass
class AssistantThinkingCompleted(BaseEvent):
    pass


@dataclass
class ResponseGenerated(BaseEvent):
    response_text: str


@dataclass
class SpeakingStarted(BaseEvent):
    pass


@dataclass
class SpeakingCompleted(BaseEvent):
    pass


@dataclass
class WakeWordDetected(BaseEvent):
    pass


@dataclass
class ListeningStarted(BaseEvent):
    pass


@dataclass
class ListeningCompleted(BaseEvent):
    transcript: str


@dataclass
class ErrorOccurred(BaseEvent):
    error_message: str
    exception: Exception | None = None


class EventBus:
    """Async publish/subscribe event bus."""

    def __init__(self) -> None:
        self._handlers: dict[Type[BaseEvent], list[Handler]] = {}

    def subscribe(self, event_type: Type[T], handler: Handler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: Type[T], handler: Handler) -> None:
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    async def publish(self, event: BaseEvent) -> None:
        handlers = self._handlers.get(type(event), [])
        if not handlers:
            return
        results = await asyncio.gather(
            *[h(event) for h in handlers], return_exceptions=True
        )
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"Event handler error for {type(event).__name__}: {r}")
