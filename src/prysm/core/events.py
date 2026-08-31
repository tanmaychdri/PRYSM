import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

EventHandler = Callable[..., Coroutine[Any, Any, None]]

class EventBus:
    """A simple asynchronous in-memory event bus."""
    def __init__(self):
        self._subscribers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe an async handler to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
            except ValueError:
                pass

    async def publish(self, event_type: str, *args: Any, **kwargs: Any) -> None:
        """Publish an event to all subscribers concurrently."""
        handlers = self._subscribers.get(event_type, [])
        if handlers:
            tasks = [handler(*args, **kwargs) for handler in handlers]
            await asyncio.gather(*tasks, return_exceptions=True)
