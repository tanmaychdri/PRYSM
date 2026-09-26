import logging
from typing import Callable, Coroutine, Any

logger = logging.getLogger(__name__)

Hook = Callable[[], Coroutine[Any, Any, None]]


class Lifecycle:
    """Manages ordered startup and shutdown hooks."""

    def __init__(self) -> None:
        self._startup_hooks: list[Hook] = []
        self._shutdown_hooks: list[Hook] = []

    def on_startup(self, hook: Hook) -> None:
        self._startup_hooks.append(hook)

    def on_shutdown(self, hook: Hook) -> None:
        self._shutdown_hooks.append(hook)

    async def start(self) -> None:
        for hook in self._startup_hooks:
            try:
                await hook()
            except Exception:
                logger.exception(f"Startup hook {hook.__name__} failed")
                raise

    async def stop(self) -> None:
        for hook in reversed(self._shutdown_hooks):
            try:
                await hook()
            except Exception:
                logger.exception(f"Shutdown hook {hook.__name__} failed")
