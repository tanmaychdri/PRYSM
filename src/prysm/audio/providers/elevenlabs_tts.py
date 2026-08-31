import asyncio
import logging
from collections.abc import AsyncGenerator

from elevenlabs.client import AsyncElevenLabs

from prysm.audio.interfaces import TextToSpeech
from prysm.config.settings import Settings

logger = logging.getLogger(__name__)


class ElevenLabsTTS(TextToSpeech):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AsyncElevenLabs(api_key=self.settings.elevenlabs_api_key)

    async def synthesize(self, text: str) -> AsyncGenerator[bytes, None]:
        if not self.settings.elevenlabs_api_key:
            logger.error("ElevenLabs API key is missing. TTS unavailable.")
            yield b""
            return

        logger.info(f"Synthesizing text: '{text[:20]}...'")
        try:
            # Use configured voice, env var, or Adam (pNInz6obpgDQGcFmaJgB) as fallback
            voice_id = self.settings.tts.voice_id or self.settings.elevenlabs_voice_id or "pNInz6obpgDQGcFmaJgB"

            audio_stream = self.client.text_to_speech.convert(
                voice_id=voice_id,
                model_id=self.settings.tts.model_id,
                text=text,
                output_format=self.settings.tts.output_format, # type: ignore
            )

            async for chunk in audio_stream:
                if chunk:
                    yield chunk

        except asyncio.CancelledError:
            logger.info("TTS Synthesis cancelled.")
            raise
        except Exception:
            logger.exception("ElevenLabs TTS Error")
            raise
