from abc import ABC, abstractmethod
from typing import AsyncIterator


class AudioCapture(ABC):
    """Interface for audio input devices."""

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def read_chunk(self) -> bytes: ...

    @abstractmethod
    def flush(self) -> None: ...


class AudioOutput(ABC):
    """Interface for audio output devices."""

    @abstractmethod
    async def play_stream(self, stream: AsyncIterator[bytes]) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...


class STTProvider(ABC):
    """Interface for speech-to-text providers."""

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes) -> str: ...


class TTSProvider(ABC):
    """Interface for text-to-speech providers."""

    @abstractmethod
    async def synthesize(self, text: str) -> AsyncIterator[bytes]:
        """Synthesize text and return an async iterator of PCM audio chunks."""
        ...
