from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any

from prysm.core.state import AssistantState


class UIProvider(ABC):
    """Abstract boundary for UI components."""
    
    @abstractmethod
    def set_on_start_callback(self, callback: Callable[[], Coroutine[Any, Any, None]]) -> None:
        pass
        
    @abstractmethod
    def set_on_stop_callback(self, callback: Callable[[], Coroutine[Any, Any, None]]) -> None:
        pass
        
    @abstractmethod
    async def update_state(self, state: AssistantState) -> None:
        pass
