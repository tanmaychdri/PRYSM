from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AudioSettings(BaseModel):
    input_device: int | None = None
    output_device: int | None = None
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 512


class WakeWordSettings(BaseModel):
    enabled: bool = True
    model: str = "prysm"
    threshold: float = 0.5


class VADSettings(BaseModel):
    enabled: bool = True
    aggressiveness: int = 2  # 0 to 3 for webrtcvad
    silence_duration: float = 1.0
    speech_start_threshold: float = 0.3
    maximum_recording_duration: float = 30.0


class STTSettings(BaseModel):
    model: str = "small"
    device: str = "auto"
    compute_type: str = "default"
    language: str | None = None


class TTSSettings(BaseModel):
    provider: str = "elevenlabs"
    voice_id: str | None = None
    model_id: str = "eleven_flash_v2_5"
    output_format: str = "pcm_16000"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "PRYSM"
    environment: str = "development"
    debug: bool = False

    audio: AudioSettings = Field(default_factory=AudioSettings)
    wakeword: WakeWordSettings = Field(default_factory=WakeWordSettings)
    vad: VADSettings = Field(default_factory=VADSettings)
    stt: STTSettings = Field(default_factory=STTSettings)
    tts: TTSSettings = Field(default_factory=TTSSettings)

    # ElevenLabs credentials (loaded from env automatically)
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )
