from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_response(self, prompt: str, context: list[dict[str, Any]]) -> str:
        """Generate a response given a prompt and context."""
        pass
