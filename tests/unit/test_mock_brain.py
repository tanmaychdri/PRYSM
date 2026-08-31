import pytest

from prysm.brain.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_mock_brain_response():
    provider = MockLLMProvider()
    response = await provider.generate_response("Hello", [])

    assert response.text == "Mock Response to: Hello"
    assert response.finish_reason == "stop"
