# Manual Hardware Testing

Automated tests in PRYSM use mock audio buffers and mock AI providers to ensure CI passes without hardware. However, real hardware testing is crucial.

## Test Procedures

### 1. Device Enumeration
```bash
uv run prysm audio devices
```
Ensures `sounddevice` can see your microphone and speakers.

### 2. Microphone Input Test
```bash
uv run prysm audio test-input
```
Speak into the mic; you should see the volume meter react.

### 3. Local STT Test
```bash
uv run prysm stt test
```
Records 5 seconds of audio and transcribes it using `faster-whisper`.

### 4. ElevenLabs TTS Test
```bash
uv run prysm tts test --text "Hello world"
```
Synthesizes and plays audio. Requires `ELEVENLABS_API_KEY`.
