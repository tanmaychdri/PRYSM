from prysm.core.container import ApplicationContainer


def test_application_container():
    from prysm.config.settings import Settings

    settings = Settings(_env_file=None)
    settings.llm_api_key = None
    container = ApplicationContainer(settings=settings)
    assert container.settings is not None
    assert container.event_bus is not None
    assert container.tool_registry is not None
    assert container.llm_provider is not None
    assert container.assistant is not None
