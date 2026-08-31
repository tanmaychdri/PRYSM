import pytest

from prysm.core.assistant import PrysmAssistant
from prysm.core.state import AssistantState


@pytest.mark.asyncio
async def test_assistant_initialization():
    assistant = PrysmAssistant()
    assert assistant.state == AssistantState.STARTING
    
    # We can test the lifecycle manually
    await assistant.lifecycle.start()
    assert assistant.state == AssistantState.IDLE
    
    await assistant.lifecycle.stop()
    assert assistant.state == AssistantState.STOPPING
