import numpy as np

from prysm.config.settings import VADSettings


class EnergyVAD:
    """Simple energy-based Voice Activity Detector."""

    def __init__(self, settings: VADSettings, sample_rate: int) -> None:
        self._threshold = settings.energy_threshold
        self._silence_frames = int(
            settings.silence_duration_ms / 1000 * sample_rate / 480
        )
        self._min_speech_frames = int(
            settings.min_speech_ms / 1000 * sample_rate / 480
        )
        self._silent_count = 0
        self._speech_count = 0
        self._in_speech = False

    def is_speech(self, audio_chunk: bytes) -> bool:
        arr = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
        rms = np.sqrt(np.mean(arr ** 2)) / 32768.0
        return rms > self._threshold

    def process(self, audio_chunk: bytes) -> tuple[bool, bool]:
        """
        Returns (is_speech_active, speech_ended).
        speech_ended is True on the frame where silence threshold is crossed.
        """
        speech = self.is_speech(audio_chunk)

        if speech:
            self._speech_count += 1
            self._silent_count = 0
            if not self._in_speech and self._speech_count >= 2:
                self._in_speech = True
        else:
            if self._in_speech:
                self._silent_count += 1
                if self._silent_count >= self._silence_frames:
                    self._in_speech = False
                    self._speech_count = 0
                    self._silent_count = 0
                    return False, True  # speech just ended

        return self._in_speech, False

    def reset(self) -> None:
        self._silent_count = 0
        self._speech_count = 0
        self._in_speech = False
