# PRYSM Audio Architecture

The voice subsystem in PRYSM uses a streaming, event-driven pipeline that integrates with the core assistant.

## Components
- **Microphone Capture**: Powered by `sounddevice`.
- **Wake Word**: Local Energy/RMS based detection (due to `openWakeWord` Python 3.12 compatibility issues).
- **VAD**: Local `webrtcvad` for silence detection.
- **STT**: Local `faster-whisper`.
- **TTS**: Cloud `ElevenLabs` streaming API.

## Privacy Model
All audio input (Wake word, VAD, STT) is processed 100% locally. Raw microphone data is NEVER sent to the cloud. Only the assistant's generated text responses are sent to ElevenLabs for synthesis.

## Setup
To use ElevenLabs, set `ELEVENLABS_API_KEY` in your `.env` file.
