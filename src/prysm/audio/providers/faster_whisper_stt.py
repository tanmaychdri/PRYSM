import asyncio
import io
import logging
import wave

from faster_whisper import WhisperModel

from prysm.audio.interfaces import SpeechToText
from prysm.config.settings import STTSettings

logger = logging.getLogger(__name__)


class FasterWhisperSTT(SpeechToText):
    def __init__(self, settings: STTSettings):
        self.settings = settings
        logger.info(
            f"Loading faster-whisper model '{self.settings.model}' on {self.settings.device}..."
        )
        self.model = WhisperModel(
            self.settings.model,
            device=self.settings.device,
            compute_type=self.settings.compute_type,
        )
        logger.info("Faster-whisper model loaded.")

    async def transcribe(self, audio_data: bytes) -> str:
        """Transcribe raw PCM 16kHz audio bytes to text."""
        if not audio_data:
            return ""

        def _transcribe():
            # Convert raw bytes to a WAV in-memory file for faster_whisper
            with io.BytesIO() as wav_io:
                with wave.open(wav_io, "wb") as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(16000)
                    wav_file.writeframes(audio_data)

                wav_io.seek(0)
                segments, info = self.model.transcribe(
                    wav_io,
                    beam_size=5,
                    language=self.settings.language,
                    vad_filter=True,
                )

                text = "".join([segment.text for segment in segments])
                return text.strip()

        # Run in thread pool to avoid blocking async loop
        return await asyncio.to_thread(_transcribe)
