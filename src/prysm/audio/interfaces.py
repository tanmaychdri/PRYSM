from abc import ABC, abstractmethod


class WakeWordEngine(ABC):
    """Abstract interface for Wake Word detection."""

    @abstractmethod
    async def listen_for_wakeword(self) -> bool:
        pass


class STTProvider(ABC):
    """Abstract interface for Speech-to-Text."""

    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> str:
        pass


class TTSProvider(ABC):
    """Abstract interface for Text-to-Speech."""

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        pass
