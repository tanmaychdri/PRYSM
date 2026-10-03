import asyncio
import logging
import re

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

# Phrases that cut off speech and return to listening. Matched against a
# transcript with punctuation stripped, so "stop!" and "stop." both hit.
# Kept to short, unambiguous commands so ordinary words inside a sentence
# ("can you stop the music") don't cut PRYSM off by accident.
STOP_PHRASES = (
    "stop",
    "stop talking",
    "stop speaking",
    "shut up",
    "be quiet",
    "quiet",
    "silence",
    "enough",
    "that's enough",
    "thats enough",
    "that is enough",
    "never mind",
    "nevermind",
    "cancel",
    "ok stop",
    "okay stop",
)

_STOP_PATTERN = re.compile(
    r"^(?:" + "|".join(re.escape(p) for p in STOP_PHRASES) + r")$"
)


def is_stop_command(transcript: str) -> bool:
    """True when the whole utterance is a request to stop talking."""
    cleaned = re.sub(r"[^a-z\s]", "", transcript.lower()).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return bool(cleaned) and _STOP_PATTERN.match(cleaned) is not None


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
        self._speaking = False
        self._barge_in: asyncio.Task | None = None

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
        """Wait for speech, transcribe it, and drive the LISTENING state transitions.

        State changes belong to the main loop only. The barge-in watcher that
        runs during playback uses `_capture_utterance` directly so it never
        touches the state machine while the assistant is SPEAKING.
        """
        transcript = await self._capture_utterance()
        if transcript is None:
            return None

        await self._event_bus.publish(ListeningCompleted(transcript=transcript))
        logger.info(f"Heard: {transcript!r}")

        # We MUST transition back to IDLE so the assistant can process the input
        await self._assistant.set_state(AssistantState.IDLE, reason="transcription complete")

        return transcript

    async def _capture_utterance(self) -> str | None:
        """Record one utterance from the mic and transcribe it. No state changes."""
        self._vad.reset()
        self._audio_in.flush()
        frames: list[bytes] = []

        # 1. Wait for speech to actually start
        speech_started = False
        while self._running:
            chunk = await self._audio_in.read_chunk()
            frames.append(chunk)
            # keep only the last ~5 frames (150ms) to catch the start of the first word
            if len(frames) > 5:
                frames.pop(0)

            is_speech, _ = self._vad.process(chunk)
            if is_speech:
                speech_started = True
                break

        if not self._running or not speech_started:
            return None

        # Only the main loop (assistant idle) owns the LISTENING state.
        if not self._speaking:
            await self._event_bus.publish(ListeningStarted())
            await self._assistant.set_state(AssistantState.LISTENING, reason="speech detected")

        # 2. Record until speech ends (or timeout)
        timeout = 15.0
        deadline = asyncio.get_event_loop().time() + timeout

        while asyncio.get_event_loop().time() < deadline:
            chunk = await self._audio_in.read_chunk()
            frames.append(chunk)
            _, speech_ended = self._vad.process(chunk)
            if speech_ended:
                break

        if not frames:
            if not self._speaking:
                await self._assistant.set_state(AssistantState.IDLE, reason="listening completed (no audio)")
            return None

        audio_data = b"".join(frames)
        transcript = await self._stt.transcribe(audio_data)
        return transcript or None

    async def _on_response_generated(self, event: ResponseGenerated) -> None:
        """Speak the assistant's response via TTS.

        While speaking, the mic stays open. If the user says "stop" (or a
        similar phrase) playback is cut off immediately and the loop returns
        to listening.
        """
        if not event.response_text:
            return
        try:
            await self._assistant.set_state(AssistantState.SPEAKING, reason="TTS")
            await self._event_bus.publish(SpeakingStarted())
            self._speaking = True
            self._barge_in = asyncio.create_task(
                self._watch_for_stop(), name="barge-in"
            )
            stream = await self._tts.synthesize(event.response_text)  # returns AsyncIterator directly
            await self._audio_out.play_stream(stream)
            await self._event_bus.publish(SpeakingCompleted())
            await self._assistant.set_state(AssistantState.IDLE, reason="TTS complete")
        except Exception:
            logger.exception("TTS playback failed")
        finally:
            self._speaking = False
            await self._stop_barge_in_watch()

    async def _watch_for_stop(self) -> None:
        """Listen during playback and cut speech off on a stop command."""
        try:
            while self._speaking and self._running:
                transcript = await self._capture_utterance()
                if not self._speaking:
                    return
                if transcript and is_stop_command(transcript):
                    logger.info(f"Stop command heard: {transcript!r} — cutting speech")
                    self._speaking = False
                    await self._audio_out.stop()
                    return
                if transcript:
                    logger.debug(f"Ignored while speaking: {transcript!r}")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Barge-in listener failed")

    async def _stop_barge_in_watch(self) -> None:
        task = self._barge_in
        self._barge_in = None
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
