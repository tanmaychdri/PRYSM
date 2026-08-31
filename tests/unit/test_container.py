from prysm.core.container import ApplicationContainer


def test_application_container():
    container = ApplicationContainer()
    assert container.settings is not None
    assert container.event_bus is not None
    assert container.tool_registry is not None
    assert container.llm_provider is not None
    assert container.assistant is not None
