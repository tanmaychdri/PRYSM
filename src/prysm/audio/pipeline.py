import asyncio
import logging

from prysm.audio.capture import SoundDeviceCapture, SoundDeviceOutput
from prysm.audio.interfaces import STTProvider, TTSProvider
from prysm.audio.vad import EnergyVAD
from prysm.audio.wakeword import EnergyWakeWordDetector
from prysm.config.settings import Settings
from prysm.core.assistant import PrysmAssistant
from prysm.core.events import (
    EventBus,
    ListeningCompleted,
    ListeningStarted,
    ResponseGenerated,
    SpeakingCompleted,
    SpeakingStarted,
    WakeWordDetected,
)
from prysm.core.state import AssistantState
from prysm.models.interactions import UserInput

logger = logging.getLogger(__name__)


class VoicePipeline:
    """
    Full voice loop:
      mic -> wake word -> VAD -> STT -> assistant.process() -> TTS -> speaker
    """

    def __init__(
        self,
        settings: Settings,
        audio_in: SoundDeviceCapture,
        audio_out: SoundDeviceOutput,
        wake_word: EnergyWakeWordDetector,
        vad: EnergyVAD,
        stt: STTProvider,
        tts: TTSProvider,
        event_bus: EventBus,
        assistant: PrysmAssistant,
    ) -> None:
        self._settings = settings
        self._audio_in = audio_in
        self._audio_out = audio_out
        self._wake_word = wake_word
        self._vad = vad
        self._stt = stt
        self._tts = tts
        self._event_bus = event_bus
        self._assistant = assistant
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        # Subscribe to TTS only when voice mode is actually running
        self._event_bus.subscribe(ResponseGenerated, self._on_response_generated)
        await self._audio_in.start()
        self._running = True
        self._task = asyncio.create_task(self._loop(), name="voice-pipeline")
        logger.info("Voice pipeline started")

    async def stop(self) -> None:
        self._running = False
        self._event_bus.unsubscribe(ResponseGenerated, self._on_response_generated)
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._audio_in.stop()
        logger.info("Voice pipeline stopped")

    async def _loop(self) -> None:
        # TODO: re-enable wake word detection when ready
        # For now, always listen — VAD handles start/end of speech
        logger.info("Listening continuously (wake word disabled)...")
        while self._running:
            try:
                transcript = await self._listen_for_speech()
                if transcript:
                    await self._event_bus.publish(WakeWordDetected())
                    user_input = UserInput(text=transcript, source="voice")
                    await self._assistant.process(user_input)

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in voice pipeline loop")
                await asyncio.sleep(0.5)

    async def _listen_for_speech(self) -> str | None:
        """Collect audio until VAD detects end of speech, then transcribe."""
        await self._event_bus.publish(ListeningStarted())
        await self._assistant.set_state(AssistantState.LISTENING, reason="wake word detected")

        self._vad.reset()
        frames: list[bytes] = []
        timeout = 10.0
        deadline = asyncio.get_event_loop().time() + timeout

        while asyncio.get_event_loop().time() < deadline:
            chunk = await self._audio_in.read_chunk()
            frames.append(chunk)
            _, speech_ended = self._vad.process(chunk)
            if speech_ended and len(frames) > 5:
                break

        if not frames:
            return None

        audio_data = b"".join(frames)
        transcript = await self._stt.transcribe(audio_data)

        await self._event_bus.publish(ListeningCompleted(transcript=transcript))
        logger.info(f"Heard: {transcript!r}")
        return transcript or None

    async def _on_response_generated(self, event: ResponseGenerated) -> None:
        """Speak the assistant's response via TTS."""
        if not event.response_text:
            return
        try:
            await self._assistant.set_state(AssistantState.SPEAKING, reason="TTS")
            await self._event_bus.publish(SpeakingStarted())
            stream = await self._tts.synthesize(event.response_text)  # returns AsyncIterator directly
            await self._audio_out.play_stream(stream)
            await self._event_bus.publish(SpeakingCompleted())
            await self._assistant.set_state(AssistantState.IDLE, reason="TTS complete")
        except Exception:
            logger.exception("TTS playback failed")
