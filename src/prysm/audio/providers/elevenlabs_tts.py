import logging
from typing import AsyncIterator

from prysm.audio.interfaces import TTSProvider
from prysm.config.settings import Settings
from prysm.core.exceptions import TTSError

logger = logging.getLogger(__name__)


class ElevenLabsTTS(TTSProvider):
    """Text-to-speech using ElevenLabs streaming API."""

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.elevenlabs_api_key
        self._voice_id = settings.elevenlabs_voice_id
        self._client = None

    def _get_client(self):
        if self._client is None:
            from elevenlabs.client import ElevenLabs
            self._client = ElevenLabs(api_key=self._api_key)
        return self._client

    async def synthesize(self, text: str) -> AsyncIterator[bytes]:
        if not self._api_key:
            raise TTSError("ELEVENLABS_API_KEY is not configured")
        if not self._voice_id:
            raise TTSError("ELEVENLABS_VOICE_ID is not configured")

        try:
            client = self._get_client()
            # SDK v2+ uses .stream() instead of .convert_as_stream()
            sync_gen = client.text_to_speech.stream(
                voice_id=self._voice_id,
                text=text,
                model_id="eleven_turbo_v2_5",
                output_format="pcm_24000",
            )
            return self._wrap_stream(sync_gen)
        except Exception as e:
            logger.exception("ElevenLabs TTS failed")
            raise TTSError(str(e)) from e

    def _wrap_stream(self, sync_gen) -> AsyncIterator[bytes]:
        """Wrap a synchronous ElevenLabs byte generator into an async iterator."""
        return _AsyncGenWrapper(sync_gen)


class _AsyncGenWrapper:
    """Runs a blocking generator on the executor so the event loop stays free."""

    def __init__(self, sync_gen) -> None:
        self._gen = sync_gen

    def __aiter__(self):
        return self

    async def __anext__(self) -> bytes:
        import asyncio
        loop = asyncio.get_running_loop()

        def _next():
            try:
                return next(self._gen)
            except StopIteration:
                return None

        chunk = await loop.run_in_executor(None, _next)
        if chunk is None:
            raise StopAsyncIteration
        return chunk
