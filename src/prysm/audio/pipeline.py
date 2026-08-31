import asyncio
import logging
import time

from prysm.audio.interfaces import (
    AudioInput,
    AudioOutput,
    SpeechToText,
    TextToSpeech,
    VoiceActivityDetector,
    WakeWordDetector,
)
from prysm.config.settings import Settings
from prysm.core.assistant import PrysmAssistant
from prysm.core.events import (
    EventBus,
    SpeechStarted,
    SpeechStopped,
    TranscriptionCompleted,
    TranscriptionFailed,
    TranscriptionStarted,
    TTSCompleted,
    TTSFailed,
    TTSInterrupted,
    TTSStarted,
    WakeWordDetected,
)
from prysm.core.state import AssistantState
from prysm.models.interactions import UserInput

logger = logging.getLogger(__name__)


class VoicePipeline:
    """Orchestrates the voice interaction flow."""

    def __init__(
        self,
        settings: Settings,
        audio_in: AudioInput,
        audio_out: AudioOutput,
        wake_word: WakeWordDetector,
        vad: VoiceActivityDetector,
        stt: SpeechToText,
        tts: TextToSpeech,
        event_bus: EventBus,
        assistant: PrysmAssistant,
    ):
        self.settings = settings
        self.audio_in = audio_in
        self.audio_out = audio_out
        self.wake_word = wake_word
        self.vad = vad
        self.stt = stt
        self.tts = tts
        self.event_bus = event_bus
        self.assistant = assistant

        self._main_task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        await self.audio_in.start()
        await self.wake_word.start()
        self._stop_event.clear()
        self._main_task = asyncio.create_task(self._run_pipeline())
        logger.info("Voice Pipeline started.")

    async def stop(self) -> None:
        self._stop_event.set()
        if self._main_task:
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass
        await self.audio_in.stop()
        await self.audio_out.stop()
        await self.wake_word.stop()
        logger.info("Voice Pipeline stopped.")

    async def _run_pipeline(self) -> None:
        try:
            while not self._stop_event.is_set():
                if self.assistant.state == AssistantState.IDLE:
                    await self._wait_for_wakeword()
                elif self.assistant.state == AssistantState.LISTENING:
                    await self._capture_speech()
                elif self.assistant.state == AssistantState.SPEAKING:
                    # Let the assistant manage state, we just wait
                    await asyncio.sleep(0.1)
                else:
                    await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass

    async def _wait_for_wakeword(self) -> None:
        """Consume audio until wake word is detected."""
        chunk = await self.audio_in.read_chunk()
        if await self.wake_word.detect(chunk):
            await self.event_bus.publish(
                WakeWordDetected(model="prysm", confidence=1.0)
            )
            await self.assistant.set_state(
                AssistantState.LISTENING, reason="Wake word detected"
            )

    async def _capture_speech(self) -> None:
        """Capture audio using VAD until silence, then transcribe."""
        frames = []
        silence_frames = 0
        speech_started = False
        start_time = time.time()

        chunks_per_sec = (
            self.settings.audio.sample_rate / self.settings.audio.chunk_size
        )
        silence_chunks_threshold = int(
            self.settings.vad.silence_duration * chunks_per_sec
        )
        max_chunks = int(self.settings.vad.maximum_recording_duration * chunks_per_sec)

        logger.info("VAD listening...")
        while len(frames) < max_chunks:
            chunk = await self.audio_in.read_chunk()
            is_speech = self.vad.is_speech(chunk)

            if is_speech:
                if not speech_started:
                    speech_started = True
                    await self.event_bus.publish(SpeechStarted())
                silence_frames = 0
                frames.append(chunk)
            else:
                if speech_started:
                    silence_frames += 1
                    frames.append(chunk)
                    if silence_frames >= silence_chunks_threshold:
                        break
                else:
                    if time.time() - start_time > 5.0:
                        logger.info("VAD timed out waiting for speech.")
                        await self.assistant.set_state(
                            AssistantState.IDLE, reason="VAD timeout"
                        )
                        return

        duration = time.time() - start_time
        await self.event_bus.publish(SpeechStopped(duration=duration))

        if not frames:
            await self.assistant.set_state(
                AssistantState.IDLE, reason="No speech captured"
            )
            return

        audio_data = b"".join(frames)

        await self.assistant.set_state(
            AssistantState.PROCESSING, reason="Speech captured, transcribing"
        )
        await self.event_bus.publish(TranscriptionStarted())

        try:
            text = await self.stt.transcribe(audio_data)
            await self.event_bus.publish(
                TranscriptionCompleted(text=text, duration=duration)
            )

            if not text:
                logger.info("Transcription empty. Returning to IDLE.")
                await self.assistant.set_state(
                    AssistantState.IDLE, reason="Empty transcription"
                )
                return

            user_input = UserInput(text=text, source="voice")

            # Transition to IDLE temporarily to allow standard `process` flow
            await self.assistant.set_state(
                AssistantState.IDLE, reason="Handing over to Core"
            )

            # Note: process() will transition IDLE -> PROCESSING -> THINKING -> RESPONDING -> IDLE
            response = await self.assistant.process(user_input)

            if response and response.text:
                await self._synthesize_and_play(response.text)

        except Exception as e:
            logger.exception("STT or Core error")
            await self.event_bus.publish(TranscriptionFailed(error=str(e)))
            await self.assistant.set_state(AssistantState.IDLE, reason="Pipeline error")

    async def _synthesize_and_play(self, text: str) -> None:
        await self.assistant.set_state(
            AssistantState.SPEAKING, reason="Starting TTS playback"
        )
        await self.event_bus.publish(TTSStarted(text=text))
        try:
            stream = self.tts.synthesize(text)
            await self.audio_out.play_stream(stream)
            await self.event_bus.publish(TTSCompleted())
        except asyncio.CancelledError:
            await self.event_bus.publish(TTSInterrupted())
            await self.audio_out.stop()
            raise
        except Exception as e:
            logger.exception("TTS playback failed")
            await self.event_bus.publish(TTSFailed(error=str(e)))
        finally:
            await self.assistant.set_state(
                AssistantState.IDLE, reason="Playback complete"
            )
