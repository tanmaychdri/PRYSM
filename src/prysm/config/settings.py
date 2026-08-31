from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings for PRYSM."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    environment: str = "development"
    debug: bool = False

    # Placeholders for domain-specific settings
    llm_api_key: str = ""
    stt_provider: str = "default"
    tts_provider: str = "default"
