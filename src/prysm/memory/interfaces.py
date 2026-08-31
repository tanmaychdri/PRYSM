from abc import ABC, abstractmethod
from typing import Any


class MemoryProvider(ABC):
    """Abstract base class for memory persistence."""

    @abstractmethod
    async def save(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    async def load(self, key: str) -> Any | None:
        pass

    @abstractmethod
    async def get_recent_history(self, limit: int = 10) -> list[dict[str, Any]]:
        pass
