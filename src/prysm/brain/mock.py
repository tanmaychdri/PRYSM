from typing import Any

from prysm.brain.provider import LLMProvider
from prysm.models.interactions import BrainResponse


class MockLLMProvider(LLMProvider):
    """A mock LLM provider for testing the core runtime without AI."""

    async def generate_response(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> BrainResponse:
        """Return a simple echo or stubbed response."""
        return BrainResponse(
            text=f"Mock Response to: {messages}",
            finish_reason="stop",
        )
