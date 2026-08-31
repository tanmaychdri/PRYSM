from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class AudioInput(ABC):
    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

    @abstractmethod
    async def read_chunk(self) -> bytes:
        pass


class AudioOutput(ABC):
    @abstractmethod
    async def play(self, audio_data: bytes) -> None:
        pass

    @abstractmethod
    async def play_stream(self, audio_stream: AsyncGenerator[bytes, None]) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass


class WakeWordDetector(ABC):
    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

    @abstractmethod
    async def detect(self, audio_chunk: bytes) -> bool:
        pass


class VoiceActivityDetector(ABC):
    @abstractmethod
    def is_speech(self, audio_chunk: bytes) -> bool:
        pass


class SpeechToText(ABC):
    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> str:
        pass


class TextToSpeech(ABC):
    @abstractmethod
    def synthesize(self, text: str) -> AsyncGenerator[bytes, None]:
        pass
