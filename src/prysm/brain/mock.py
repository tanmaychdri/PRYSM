from typing import Any

from prysm.brain.provider import LLMProvider
from prysm.models.interactions import BrainResponse


class MockLLMProvider(LLMProvider):
    """A mock LLM provider for testing the core runtime without AI."""

    async def generate_response(
        self, prompt: str, context: list[dict[str, Any]]
    ) -> BrainResponse:
        """Return a simple echo or stubbed response."""
        return BrainResponse(
            text=f"Mock Response to: {prompt}",
            finish_reason="stop",
        )
