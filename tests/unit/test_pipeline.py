import pytest

from prysm.core.container import ApplicationContainer
from prysm.core.state import AssistantState
from prysm.models.interactions import UserInput


@pytest.mark.asyncio
async def test_assistant_process_pipeline():
    container = ApplicationContainer()
    assistant = container.assistant
    await assistant.lifecycle.start()

    assert assistant.state == AssistantState.IDLE

    user_input = UserInput(text="Hello")
    response = await assistant.process(user_input)

    assert response is not None
    assert "Mock Response to: Hello" in response.text

    assert assistant.state == AssistantState.IDLE
    await assistant.stop()


@pytest.mark.asyncio
async def test_assistant_invalid_state_transition():
    container = ApplicationContainer()
    assistant = container.assistant
    await assistant.lifecycle.start()

    with pytest.raises(RuntimeError, match="Invalid transition"):
        await assistant.set_state(AssistantState.SPEAKING)

    await assistant.stop()
