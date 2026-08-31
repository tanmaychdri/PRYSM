import asyncio

import pytest

from prysm.audio.interfaces import (
    AudioInput,
    AudioOutput,
    SpeechToText,
    TextToSpeech,
    VoiceActivityDetector,
    WakeWordDetector,
)
from prysm.audio.pipeline import VoicePipeline
from prysm.brain.provider import LLMProvider
from prysm.config.settings import Settings
from prysm.core.assistant import PrysmAssistant
from prysm.core.events import EventBus
from prysm.models.interactions import BrainResponse


class FakeAudioInput(AudioInput):
    def __init__(self):
        self.queue = asyncio.Queue()
        self.running = False

    async def start(self):
        self.running = True

    async def stop(self):
        self.running = False

    async def read_chunk(self):
        return await self.queue.get()


class FakeAudioOutput(AudioOutput):
    def __init__(self):
        self.played = []

    async def play(self, data):
        self.played.append(data)

    async def play_stream(self, stream):
        async for chunk in stream:
            self.played.append(chunk)

    async def stop(self):
        pass


class FakeWakeWord(WakeWordDetector):
    def __init__(self):
        self.should_detect = False

    async def start(self):
        pass

    async def stop(self):
        pass

    async def detect(self, chunk):
        return self.should_detect


class FakeVAD(VoiceActivityDetector):
    def __init__(self):
        self.speech = False

    def is_speech(self, chunk):
        return self.speech


class FakeSTT(SpeechToText):
    async def transcribe(self, data):
        return "fake transcription"


class FakeTTS(TextToSpeech):
    async def synthesize(self, text):
        yield b"fake_audio"


class FakeBrain(LLMProvider):
    async def generate_response(self, p, c):
        return BrainResponse(text="fake brain response")


@pytest.mark.asyncio
async def test_voice_pipeline_end_to_end():
    from prysm.brain.context import ContextManager
    from prysm.tools.executor import ToolExecutor
    from prysm.tools.registry import ToolRegistry

    settings = Settings()
    # Speed up tests
    settings.vad.silence_duration = 0.05
    settings.audio.chunk_size = 512

    bus = EventBus()
    reg = ToolRegistry()
    ctx = ContextManager()
    exe = ToolExecutor(reg)
    assistant = PrysmAssistant(bus, reg, FakeBrain(), ctx, exe)  # type: ignore
    await assistant.lifecycle.start()

    audio_in = FakeAudioInput()
    audio_out = FakeAudioOutput()
    wake = FakeWakeWord()
    vad = FakeVAD()
    stt = FakeSTT()
    tts = FakeTTS()

    pipeline = VoicePipeline(
        settings, audio_in, audio_out, wake, vad, stt, tts, bus, assistant
    )
    await pipeline.start()

    # 1. Trigger Wake Word
    wake.should_detect = True
    await audio_in.queue.put(b"wake")
    await asyncio.sleep(0.1)

    assert assistant.state.name == "LISTENING"

    # 2. Trigger Speech
    wake.should_detect = False
    vad.speech = True
    await audio_in.queue.put(b"speech1")
    await asyncio.sleep(0.1)

    # 3. Trigger Silence Timeout
    vad.speech = False
    # To hit 0.05s timeout at 31 chunks/sec, we just need ~2 chunks. We send 5.
    for _ in range(5):
        await audio_in.queue.put(b"silence")

    await asyncio.sleep(0.3)

    # Pipeline should have transcribed, called brain, generated TTS, and played it.
    assert b"fake_audio" in audio_out.played

    await pipeline.stop()
    await assistant.stop()
