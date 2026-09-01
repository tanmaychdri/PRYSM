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

        # Import Platform Services
        from prysm.platform.windows.applications import WindowsApplicationService
        from prysm.platform.windows.audio import WindowsAudioController
        from prysm.platform.windows.displays import WindowsDisplayService
        from prysm.platform.windows.files import WindowsFileController
        from prysm.platform.windows.power import WindowsPowerController
        from prysm.platform.windows.processes import WindowsProcessController
        from prysm.platform.windows.system import WindowsSystemService
        from prysm.platform.windows.windows import WindowsWindowService
        from prysm.platform.windows.workspaces import WindowsWorkspaceService
        from prysm.tools.executor import ToolExecutor

        self.settings = settings or Settings()
        self.event_bus = EventBus()
        self.tool_registry = ToolRegistry()
        from prysm.mobile.service import MobileService

        self.mobile_service = MobileService(self.event_bus)

        # Init OS Services
        self.audio_svc = WindowsAudioController()
        self.app_svc = WindowsApplicationService()
        self.proc_svc = WindowsProcessController()
        self.power_svc = WindowsPowerController()
        self.file_svc = WindowsFileController()
        self.window_svc = WindowsWindowService()
        self.display_svc = WindowsDisplayService()
        self.system_svc = WindowsSystemService()
        self.workspace_svc = WindowsWorkspaceService(self.app_svc, self.window_svc)

        # Register OS Tools
        from prysm.tools.os.app import OsAppTools
        from prysm.tools.os.audio import OsAudioTools
        from prysm.tools.os.display import OsDisplayTools
        from prysm.tools.os.file import OsFileTools
        from prysm.tools.os.power import OsPowerTools
        from prysm.tools.os.process import OsProcessTools
        from prysm.tools.os.system import OsSystemTools
        from prysm.tools.os.window import OsWindowTools
        from prysm.tools.os.workspace import OsWorkspaceTools

        OsAppTools(self.app_svc).register(self.tool_registry)
        OsAudioTools(self.audio_svc).register(self.tool_registry)
        OsDisplayTools(self.display_svc).register(self.tool_registry)
        OsFileTools(self.file_svc).register(self.tool_registry)
        OsPowerTools(self.power_svc).register(self.tool_registry)
        OsProcessTools(self.proc_svc).register(self.tool_registry)
        OsSystemTools(self.system_svc).register(self.tool_registry)
        OsWindowTools(self.window_svc).register(self.tool_registry)
        OsWorkspaceTools(self.workspace_svc).register(self.tool_registry)

        # Time tool is now registered inside OsSystemTools


        # Register Mobile Tools
        from prysm.tools.mobile.device import MobileDeviceTools
        from prysm.tools.mobile.location import MobileLocationTools
        from prysm.tools.mobile.notification import MobileNotificationTools
        from prysm.tools.mobile.sms import MobileSmsTools

        MobileDeviceTools(self.mobile_service).register(self.tool_registry)
        MobileSmsTools(self.mobile_service).register(self.tool_registry)
        MobileNotificationTools(self.mobile_service).register(self.tool_registry)
        MobileLocationTools(self.mobile_service).register(self.tool_registry)

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
