import asyncio
import logging
from typing import AsyncIterator

import numpy as np
import sounddevice as sd

from prysm.audio.interfaces import AudioCapture, AudioOutput
from prysm.config.settings import AudioSettings
from prysm.core.exceptions import AudioError

logger = logging.getLogger(__name__)


class SoundDeviceCapture(AudioCapture):
    """Microphone capture using sounddevice."""

    def __init__(self, settings: AudioSettings) -> None:
        self._settings = settings
        self._queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=2000)
        self._stream: sd.InputStream | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._stream = sd.InputStream(
            samplerate=self._settings.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=self._settings.chunk_frames,
            device=self._settings.input_device,
            callback=self._callback,
        )
        self._stream.start()
        logger.info("Audio capture started")

    async def stop(self) -> None:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        logger.info("Audio capture stopped")

    async def read_chunk(self) -> bytes:
        return await self._queue.get()

    def flush(self) -> None:
        """Discard all pending audio chunks in the queue."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    def _callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        if status:
            logger.warning(f"Audio capture status: {status}")
        if self._loop and not self._loop.is_closed():
            try:
                self._loop.call_soon_threadsafe(
                    self._queue.put_nowait, indata.tobytes()
                )
            except asyncio.QueueFull:
                pass  # Drop frame if queue is full


class SoundDeviceOutput(AudioOutput):
    """Speaker output using sounddevice."""

    def __init__(self, settings: AudioSettings) -> None:
        self._settings = settings
        self._current_stream: sd.OutputStream | None = None

    async def play_stream(self, stream: AsyncIterator[bytes]) -> None:
        loop = asyncio.get_running_loop()
        out = sd.OutputStream(
            samplerate=24000,  # ElevenLabs outputs 24kHz PCM
            channels=1,
            dtype="int16",
            device=self._settings.output_device,
        )
        out.start()
        self._current_stream = out
        try:
            async for chunk in stream:
                if chunk:
                    arr = np.frombuffer(chunk, dtype=np.int16)
                    await loop.run_in_executor(None, out.write, arr)
        finally:
            out.stop()
            out.close()
            self._current_stream = None

    async def stop(self) -> None:
        if self._current_stream:
            self._current_stream.stop()
