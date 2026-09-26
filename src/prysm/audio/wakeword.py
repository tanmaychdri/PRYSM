import logging

import numpy as np

from prysm.config.settings import WakeWordSettings

logger = logging.getLogger(__name__)


class EnergyWakeWordDetector:
    """
    Lightweight energy-spike wake word detector.
    For production, swap this with a real model (e.g. openWakeWord).
    This version triggers on a sustained loud burst — good enough for dev.
    """

    def __init__(self, settings: WakeWordSettings) -> None:
        self._threshold = settings.energy_threshold
        self._phrase = settings.phrase.lower()
        self._burst_count = 0
        self._required_bursts = 6  # ~180ms of loud audio at 30ms chunks

    def detect(self, audio_chunk: bytes) -> bool:
        arr = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
        rms = np.sqrt(np.mean(arr ** 2)) / 32768.0

        if rms > self._threshold:
            self._burst_count += 1
        else:
            self._burst_count = max(0, self._burst_count - 1)

        if self._burst_count >= self._required_bursts:
            self._burst_count = 0
            logger.info("Wake word detected (energy trigger)")
            return True
        return False

    def reset(self) -> None:
        self._burst_count = 0
