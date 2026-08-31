from prysm.audio.capture import SoundDeviceCapture, SoundDeviceOutput
from prysm.audio.pipeline import VoicePipeline
from prysm.audio.providers.elevenlabs_tts import ElevenLabsTTS
from prysm.audio.providers.faster_whisper_stt import FasterWhisperSTT
from prysm.audio.vad import EnergyVADDetector
from prysm.audio.wakeword import EnergyWakeWordDetector
from prysm.brain.mock import MockLLMProvider
from prysm.config.settings import Settings
from prysm.core.assistant import PrysmAssistant
from prysm.core.events import EventBus
from prysm.tools.registry import ToolRegistry


class ApplicationContainer:
    """Central Dependency Injection container."""

    def __init__(self, settings: Settings | None = None):
        from prysm.brain.context import ContextManager
        from prysm.brain.providers.openai_provider import OpenAILLMProvider
        from prysm.platform.windows.applications import WindowsApplicationController

        # Import Platform Controllers
        from prysm.platform.windows.audio import WindowsAudioController
        from prysm.platform.windows.files import WindowsFileController
        from prysm.platform.windows.power import WindowsPowerController
        from prysm.platform.windows.processes import WindowsProcessController
        from prysm.tools.executor import ToolExecutor
        from prysm.tools.system.applications import (
            SystemAppCloseTool,
            SystemAppLaunchTool,
        )
        from prysm.tools.system.files import (
            SystemFileSearchTool,
            SystemRecycleBinEmptyTool,
        )

        # Import System Tools
        from prysm.tools.system.info import SystemInfoTool, SystemTimeGetTool
        from prysm.tools.system.power import (
            SystemPowerRestartTool,
            SystemPowerShutdownTool,
            SystemPowerSleepTool,
            SystemScreenLockTool,
        )
        from prysm.tools.system.processes import (
            SystemProcessGetTool,
            SystemProcessKillTool,
            SystemProcessListTool,
        )
        from prysm.tools.system.volume import (
            SystemVolumeGetTool,
            SystemVolumeMuteTool,
            SystemVolumeSetTool,
        )

        self.settings = settings or Settings()
        self.event_bus = EventBus()
        self.tool_registry = ToolRegistry()

        # Init OS Controllers
        self.audio_ctrl = WindowsAudioController()
        self.app_ctrl = WindowsApplicationController()
        self.proc_ctrl = WindowsProcessController()
        self.power_ctrl = WindowsPowerController()
        self.file_ctrl = WindowsFileController()

        # Register Built-in Tools
        self.tool_registry.register(SystemTimeGetTool())
        self.tool_registry.register(SystemInfoTool())

        self.tool_registry.register(SystemVolumeGetTool(self.audio_ctrl))
        self.tool_registry.register(SystemVolumeSetTool(self.audio_ctrl))
        self.tool_registry.register(SystemVolumeMuteTool(self.audio_ctrl))

        self.tool_registry.register(SystemAppLaunchTool(self.app_ctrl))
        self.tool_registry.register(SystemAppCloseTool(self.app_ctrl))

        self.tool_registry.register(SystemProcessListTool(self.proc_ctrl))
        self.tool_registry.register(SystemProcessGetTool(self.proc_ctrl))
        self.tool_registry.register(SystemProcessKillTool(self.proc_ctrl))

        self.tool_registry.register(SystemPowerSleepTool(self.power_ctrl))
        self.tool_registry.register(SystemPowerRestartTool(self.power_ctrl))
        self.tool_registry.register(SystemPowerShutdownTool(self.power_ctrl))
        self.tool_registry.register(SystemScreenLockTool(self.power_ctrl))

        self.tool_registry.register(SystemRecycleBinEmptyTool(self.file_ctrl))
        self.tool_registry.register(SystemFileSearchTool(self.file_ctrl))

        self.context_manager = ContextManager()
        self.tool_executor = ToolExecutor(self.tool_registry)

        # Wire LLM Provider
        if self.settings.llm_api_key:
            self.llm_provider = OpenAILLMProvider(
                api_key=self.settings.llm_api_key,
                model=self.settings.llm_model,
                base_url=self.settings.llm_base_url,
            )
        else:
            self.llm_provider = MockLLMProvider()

        self.assistant = PrysmAssistant(
            event_bus=self.event_bus,
            tool_registry=self.tool_registry,
            llm_provider=self.llm_provider,
            context_manager=self.context_manager,
            tool_executor=self.tool_executor,
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
