from abc import ABC, abstractmethod
from typing import Any

from prysm.models.interactions import BrainResponse


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate_response(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> BrainResponse:
        """Generate a response given a context of normalized messages and tools."""
        pass
