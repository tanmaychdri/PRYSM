import numpy as np
import logging
from prysm.audio.interfaces import VoiceActivityDetector
from prysm.config.settings import VADSettings

logger = logging.getLogger(__name__)

class EnergyVADDetector(VoiceActivityDetector):
    """
    A fallback VAD based on audio energy (RMS).
    Used because webrtcvad relies on deprecated pkg_resources which breaks in Python 3.12+.
    """
    
    def __init__(self, settings: VADSettings, sample_rate: int = 16000):
        self.settings = settings
        self.sample_rate = sample_rate
        # A simple energy threshold for speech vs silence
        self._threshold = max(0.01, self.settings.speech_start_threshold * 0.1)
        
    def is_speech(self, audio_chunk: bytes) -> bool:
        if not self.settings.enabled:
            return True
            
        audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
        if len(audio_array) == 0:
            return False
            
        rms = np.sqrt(np.mean(audio_array.astype(np.float32)**2))
        normalized_energy = float(rms / 32768.0)
        
        return normalized_energy > self._threshold
