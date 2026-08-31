from prysm.audio.capture import SoundDeviceCapture, SoundDeviceOutput
from prysm.audio.pipeline import VoicePipeline
from prysm.audio.providers.elevenlabs_tts import ElevenLabsTTS
from prysm.audio.providers.faster_whisper_stt import FasterWhisperSTT
from prysm.audio.vad import EnergyVADDetector
from prysm.audio.wakeword import EnergyWakeWordDetector
from prysm.brain.mock import MockLLMProvider
from prysm.brain.provider import LLMProvider
from prysm.config.settings import Settings
from prysm.core.assistant import PrysmAssistant
from prysm.core.events import EventBus
from prysm.tools.registry import ToolRegistry


class ApplicationContainer:
    """Central Dependency Injection container."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.event_bus = EventBus()
        self.tool_registry = ToolRegistry()
        self.llm_provider: LLMProvider = MockLLMProvider()

        self.assistant = PrysmAssistant(
            event_bus=self.event_bus,
            tool_registry=self.tool_registry,
            llm_provider=self.llm_provider,
        )

        # Audio Pipeline
        self.audio_in = SoundDeviceCapture(self.settings.audio)
        self.audio_out = SoundDeviceOutput(self.settings.audio)
        self.wake_word = EnergyWakeWordDetector(self.settings.wakeword)
        self.vad = EnergyVADDetector(self.settings.vad, self.settings.audio.sample_rate)

        # In a real app we might load these lazily to avoid delay, but for now init here.
        self.stt = FasterWhisperSTT(self.settings.stt)
        self.tts = ElevenLabsTTS(self.settings)

        self.voice_pipeline = VoicePipeline(
            settings=self.settings,
            audio_in=self.audio_in,
            audio_out=self.audio_out,
            wake_word=self.wake_word,
            vad=self.vad,
            stt=self.stt,
            tts=self.tts,
            event_bus=self.event_bus,
            assistant=self.assistant,
        )
