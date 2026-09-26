from abc import ABC, abstractmethod
from typing import Any

from prysm.models.interactions import BrainResponse, LLMMessage


class LLMProvider(ABC):
    """Abstract interface for all LLM backends."""

    @abstractmethod
    async def generate_response(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> BrainResponse:
        """Generate a response given a message history and optional tool schemas."""
        ...
