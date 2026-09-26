# PRYSM

A modular, async-first personal AI assistant for Windows.

## Features

- **Voice mode** — wake word → WhisperFlow STT → LLM → ElevenLabs TTS
- **Chat mode** — interactive terminal chat
- **Chat UI** — tkinter-based chat window
- **OS tools** — system info, app launcher, power control, volume, clipboard
- **OpenAI-compatible LLM** — works with OpenAI, Groq, Ollama, etc.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy .env.example .env
# Edit .env with your API keys
```

## Usage

```powershell
prysm voice                          # Full voice mode
prysm chat                           # Terminal chat
python -m prysm.ui.chat_window       # Chat UI window
prysm audio devices                  # List audio devices
prysm audio test-mic                 # Mic volume meter
prysm stt test                       # Record 5s + transcribe
prysm tts test --text "Hello"        # TTS playback test
```

## Architecture

```
src/prysm/
├── config/         Settings (pydantic-settings, reads .env)
├── models/         Pydantic data models
├── core/           Assistant, EventBus, state machine, lifecycle, DI container
├── brain/          LLM provider + context manager
├── audio/          Capture, output, VAD, wake word, voice pipeline
│   └── providers/  FasterWhisper STT, ElevenLabs TTS
├── tools/          Registry, executor, tool interface
│   └── os/         Windows OS tools
└── ui/             tkinter chat window
```

## Adding a Tool

1. Create a class in `src/prysm/tools/os/` extending `BaseTool`
2. Implement `get_schemas()` and `execute()`
3. Register it in `src/prysm/core/container.py`

## Tests

```powershell
pytest
```