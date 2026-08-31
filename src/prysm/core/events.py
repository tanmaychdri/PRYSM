import asyncio
import inspect
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, TypeVar
from uuid import UUID, uuid4


@dataclass(kw_only=True)
class Event:
    """Base event class."""

    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID | None = None


@dataclass(kw_only=True)
class ApplicationStarted(Event):
    pass


@dataclass(kw_only=True)
class ApplicationStopping(Event):
    pass


@dataclass(kw_only=True)
class ApplicationStopped(Event):
    pass


@dataclass(kw_only=True)
class StateChanged(Event):
    previous_state: Any  # Any to avoid circular import, handled in assistant
    new_state: Any
    reason: str | None = None


@dataclass(kw_only=True)
class InputReceived(Event):
    input_text: str
    source: str


@dataclass(kw_only=True)
class ProcessingStarted(Event):
    pass


@dataclass(kw_only=True)
class ProcessingCompleted(Event):
    pass


@dataclass(kw_only=True)
class AssistantThinkingStarted(Event):
    pass


@dataclass(kw_only=True)
class AssistantThinkingCompleted(Event):
    pass


@dataclass(kw_only=True)
class ResponseGenerated(Event):
    response_text: str


@dataclass(kw_only=True)
class ErrorOccurred(Event):
    error_message: str
    exception: Exception | None = None


@dataclass(kw_only=True)
class WakeWordDetected(Event):
    model: str
    confidence: float


@dataclass(kw_only=True)
class SpeechStarted(Event):
    pass


@dataclass(kw_only=True)
class SpeechStopped(Event):
    duration: float


@dataclass(kw_only=True)
class TranscriptionStarted(Event):
    pass


@dataclass(kw_only=True)
class TranscriptionCompleted(Event):
    text: str
    duration: float
    language: str | None = None


@dataclass(kw_only=True)
class TranscriptionFailed(Event):
    error: str


@dataclass(kw_only=True)
class TTSStarted(Event):
    text: str


@dataclass(kw_only=True)
class TTSCompleted(Event):
    pass


@dataclass(kw_only=True)
class TTSInterrupted(Event):
    pass


@dataclass(kw_only=True)
class TTSFailed(Event):
    error: str


@dataclass(kw_only=True)
class MobileEvent(Event):
    event_type: str
    payload: dict[str, Any]


E = TypeVar("E", bound=Event)
EventHandler = Callable[[E], Coroutine[Any, Any, None] | None]


class EventBus:
    """An asynchronous in-memory event bus with typed events."""

    def __init__(self):
        self._subscribers: dict[type[Event], list[EventHandler[Event]]] = {}

    def subscribe(self, event_type: type[E], handler: EventHandler[E]) -> None:
        """Subscribe a sync or async handler to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)  # type: ignore

    def unsubscribe(self, event_type: type[E], handler: EventHandler[E]) -> None:
        """Unsubscribe a handler from an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)  # type: ignore
            except ValueError:
                pass

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers concurrently."""
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])
        if not handlers:
            return

        async def _run_handler(h: EventHandler[Event]):
            res = h(event)
            if inspect.iscoroutine(res):
                await res

        tasks = [_run_handler(handler) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)
