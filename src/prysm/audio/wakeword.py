import logging

import numpy as np

from prysm.audio.interfaces import WakeWordDetector
from prysm.config.settings import WakeWordSettings

logger = logging.getLogger(__name__)


class EnergyWakeWordDetector(WakeWordDetector):
    """
    A fallback wake word detector based on audio energy (RMS).
    Used because openWakeWord is incompatible with Python 3.12 dependencies
    (tflite-runtime).
    """

    def __init__(self, settings: WakeWordSettings):
        self.settings = settings
        self.is_running = False
        # Lower threshold since voice might not peak to 32768
        self._internal_threshold = max(0.01, settings.threshold * 0.1)

    async def start(self) -> None:
        self.is_running = True
        logger.info(
            f"Started Energy Wake Word Detector (Threshold: {self._internal_threshold:.3f})"
        )

    async def stop(self) -> None:
        self.is_running = False
        logger.info("Stopped Wake Word Detector")

    async def detect(self, audio_chunk: bytes) -> bool:
        if not self.is_running or not self.settings.enabled:
            return False

        audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
        if len(audio_array) == 0:
            return False

        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))

        # Normalize to 0-1 range roughly assuming int16 max is 32768
        normalized_energy = float(rms / 32768.0)

        if normalized_energy > self._internal_threshold:
            logger.info(
                f"Wake energy detected: {normalized_energy:.3f} > {self._internal_threshold:.3f}"
            )
            return True

        return False
