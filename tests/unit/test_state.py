from prysm.core.state import AssistantState


def test_assistant_state_enum():
    assert AssistantState.IDLE.name == "IDLE"
    assert AssistantState.STARTING.name == "STARTING"
