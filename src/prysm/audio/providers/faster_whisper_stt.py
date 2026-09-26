import logging
from io import BytesIO

import numpy as np

from prysm.audio.interfaces import STTProvider
from prysm.config.settings import STTSettings
from prysm.core.exceptions import STTError

logger = logging.getLogger(__name__)


class FasterWhisperSTT(STTProvider):
    """Speech-to-text using faster-whisper (WhisperFlow)."""

    def __init__(self, settings: STTSettings) -> None:
        self._settings = settings
        self._model = None

    def _load_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            logger.info(f"Loading Whisper model '{self._settings.model}' on {self._settings.device}...")
            self._model = WhisperModel(
                self._settings.model,
                device=self._settings.device,
                compute_type="int8",
            )
            logger.info("Whisper model loaded.")
        return self._model

    async def transcribe(self, audio_bytes: bytes) -> str:
        try:
            import asyncio
            model = self._load_model()
            arr = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

            # Run the heavy, synchronous transcribe call in a background thread 
            # to avoid freezing the event loop and dropping audio frames.
            segments, _ = await asyncio.to_thread(
                model.transcribe,
                arr,
                language=self._settings.language,
                beam_size=5,
                vad_filter=True,
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
            logger.debug(f"Transcribed: {text!r}")
            return text
        except Exception as e:
            logger.exception("STT transcription failed")
            raise STTError(str(e)) from e
