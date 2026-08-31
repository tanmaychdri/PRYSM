# PRYSM

A modular, async-first personal AI assistant.

## Setup
Ensure you have `uv` installed.
```bash
uv sync
```
Set your `.env` for ElevenLabs (optional):
```bash
ELEVENLABS_API_KEY=your_key
```

## Voice Architecture
```text
Microphone -> Local Wake Word -> Local VAD -> Local faster-whisper -> PRYSM Core -> ElevenLabs TTS -> Speaker
```
*Speech recognition is processed locally with faster-whisper, while ElevenLabs is used for high-quality voice synthesis.*

## Running Development Chat
```bash
uv run prysm chat
```