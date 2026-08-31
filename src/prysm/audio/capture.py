import asyncio
from collections.abc import AsyncGenerator

import numpy as np
import sounddevice as sd

from prysm.audio.interfaces import AudioInput, AudioOutput
from prysm.config.settings import AudioSettings


class SoundDeviceCapture(AudioInput):
    """Captures microphone input using python-sounddevice."""

    def __init__(self, settings: AudioSettings):
        self.settings = settings
        self.queue: asyncio.Queue[bytes] = asyncio.Queue()
        self.stream: sd.InputStream | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def _audio_callback(
        self, indata: np.ndarray, frames: int, time, status: sd.CallbackFlags
    ) -> None:
        if status:
            # We log this via standard print for the callback thread, ideally use logger
            pass

        audio_bytes = indata.tobytes()
        if self._loop:
            self._loop.call_soon_threadsafe(self.queue.put_nowait, audio_bytes)

    async def start(self) -> None:
        if self.stream is not None:
            return

        self._loop = asyncio.get_running_loop()
        self.stream = sd.InputStream(
            device=self.settings.input_device,
            channels=self.settings.channels,
            samplerate=self.settings.sample_rate,
            dtype="int16",
            blocksize=self.settings.chunk_size,
            callback=self._audio_callback,
        )
        self.stream.start()

    async def stop(self) -> None:
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    async def read_chunk(self) -> bytes:
        return await self.queue.get()


class SoundDeviceOutput(AudioOutput):
    """Plays audio using python-sounddevice."""

    def __init__(self, settings: AudioSettings):
        self.settings = settings
        self._stop_event = asyncio.Event()

    async def play(self, audio_data: bytes) -> None:
        self._stop_event.clear()
        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        # We run the blocking play in a thread so it doesn't freeze the loop,
        # but we can't easily interrupt sd.play().
        # For interruptible, we should use OutputStream.
        await asyncio.to_thread(self._play_sync, audio_array)

    def _play_sync(self, audio_array: np.ndarray) -> None:
        sd.play(audio_array, samplerate=self.settings.sample_rate, blocking=True)

    async def play_stream(self, audio_stream: AsyncGenerator[bytes, None]) -> None:
        self._stop_event.clear()

        stream = sd.RawOutputStream(
            samplerate=self.settings.sample_rate,
            channels=self.settings.channels,
            dtype="int16",
        )
        stream.start()

        buffer = bytearray()

        try:
            async for chunk in audio_stream:
                if self._stop_event.is_set():
                    break
                if chunk:
                    buffer.extend(chunk)
                    # Write in chunks (minimum 4096 bytes) and ensure multiples of 2 bytes
                    if len(buffer) >= 4096:
                        write_len = len(buffer) - (len(buffer) % 2)
                        to_write = bytes(buffer[:write_len])
                        del buffer[:write_len]
                        await asyncio.to_thread(stream.write, to_write)

            # Write any remaining bytes (must be multiple of 2)
            if len(buffer) >= 2:
                write_len = len(buffer) - (len(buffer) % 2)
                await asyncio.to_thread(stream.write, bytes(buffer[:write_len]))

        finally:
            stream.stop()
            stream.close()

    async def stop(self) -> None:
        self._stop_event.set()
        sd.stop()
