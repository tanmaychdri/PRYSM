import logging

from prysm.audio.capture import SoundDeviceCapture, SoundDeviceOutput
from prysm.audio.pipeline import VoicePipeline
from prysm.audio.providers.elevenlabs_tts import ElevenLabsTTS
from prysm.audio.providers.faster_whisper_stt import FasterWhisperSTT
from prysm.audio.vad import EnergyVAD
from prysm.audio.wakeword import EnergyWakeWordDetector
from prysm.brain.context import ContextManager
from prysm.brain.providers.openai_provider import OpenAILLMProvider
from prysm.config.settings import Settings
from prysm.core.assistant import PrysmAssistant
from prysm.core.events import EventBus
from prysm.tools.executor import ToolExecutor
from prysm.tools.os.app import OsAppTools
from prysm.tools.os.clipboard import OsClipboardTools
from prysm.tools.os.power import OsPowerTools
from prysm.tools.os.system import OsSystemTools
from prysm.tools.os.volume import OsVolumeTools
from prysm.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class ApplicationContainer:
    """
    Dependency injection container.
    Wires all concrete implementations together.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

        # Core infrastructure
        self.event_bus = EventBus()
        self.tool_registry = ToolRegistry()

        # Register OS tools
        OsSystemTools().register(self.tool_registry)
        OsAppTools().register(self.tool_registry)
        OsPowerTools().register(self.tool_registry)
        OsVolumeTools().register(self.tool_registry)
        OsClipboardTools().register(self.tool_registry)

        # Brain
        self.context_manager = ContextManager()
        self.tool_executor = ToolExecutor(self.tool_registry)
        self.llm_provider = OpenAILLMProvider(
            api_key=self.settings.llm_api_key,
            model=self.settings.llm_model,
            base_url=self.settings.llm_base_url,
        )

        # Assistant
        self.assistant = PrysmAssistant(
            event_bus=self.event_bus,
            tool_registry=self.tool_registry,
            llm_provider=self.llm_provider,
            context_manager=self.context_manager,
            tool_executor=self.tool_executor,
        )

        # Audio
        self.audio_in = SoundDeviceCapture(self.settings.audio)
        self.audio_out = SoundDeviceOutput(self.settings.audio)
        self.wake_word = EnergyWakeWordDetector(self.settings.wakeword)
        self.vad = EnergyVAD(self.settings.vad, self.settings.audio.sample_rate)
        self.stt = FasterWhisperSTT(self.settings.stt)
        self.tts = ElevenLabsTTS(self.settings)

        # Voice pipeline
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

        logger.info(
            f"Container ready | LLM: {self.settings.llm_model} | "
            f"STT: {self.settings.stt.model} | "
            f"Tools: {len(self.tool_registry.list_tools())}"
        )
