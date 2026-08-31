import os

from prysm.config.settings import Settings


def test_settings_default():
    # Ensure environment variables don't bleed into the test
    os.environ.pop("ENVIRONMENT", None)
    os.environ.pop("DEBUG", None)
    settings = Settings()
    assert settings.environment == "development"
    assert settings.debug is False
