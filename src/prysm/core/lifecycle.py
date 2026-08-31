from collections.abc import Callable, Coroutine

Hook = Callable[[], Coroutine[None, None, None]]


class Lifecycle:
    """Manages application startup and shutdown lifecycle hooks."""

    def __init__(self):
        self._startup_hooks: list[Hook] = []
        self._shutdown_hooks: list[Hook] = []

    def on_startup(self, hook: Hook) -> None:
        self._startup_hooks.append(hook)

    def on_shutdown(self, hook: Hook) -> None:
        self._shutdown_hooks.append(hook)

    async def start(self) -> None:
        for hook in self._startup_hooks:
            await hook()

    async def stop(self) -> None:
        for hook in self._shutdown_hooks:
            await hook()
