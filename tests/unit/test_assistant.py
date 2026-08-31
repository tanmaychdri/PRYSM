import pytest

from prysm.core.container import ApplicationContainer
from prysm.core.state import AssistantState


@pytest.mark.asyncio
async def test_assistant_initialization():
    from prysm.config.settings import Settings

    settings = Settings(_env_file=None)
    settings.llm_api_key = None
    container = ApplicationContainer(settings=settings)
    assistant = container.assistant

    assert assistant.state == AssistantState.STARTING

    await assistant.lifecycle.start()
    assert assistant.state == AssistantState.IDLE

    await assistant.lifecycle.stop()
    assert assistant.state == AssistantState.STOPPED


@pytest.mark.asyncio
async def test_assistant_double_stop():
    from prysm.config.settings import Settings

    settings = Settings(_env_file=None)
    settings.llm_api_key = None
    container = ApplicationContainer(settings=settings)
    assistant = container.assistant
    await assistant.lifecycle.start()

    await assistant.stop()
    assert assistant.state == AssistantState.STOPPED

    # Second stop should not crash
    await assistant.stop()
    assert assistant.state == AssistantState.STOPPED
