# PRYSM

A modular, async-first personal AI assistant built in Python.

## Core Architecture
PRYSM is designed with an event-driven architecture that currently supports:
1. **Local Audio Pipeline**: Microphone -> Local Wake Word -> Local VAD -> Local faster-whisper.
2. **Agentic LLM Brain**: An intelligent Tool-Calling loop that manages conversational memory and executes dynamic system tools safely.
3. **Voice Synthesis**: ElevenLabs TTS integration.

## Setup
Ensure you have `uv` installed.
```bash
uv sync
```
Set up your environment variables by copying `.env.example` to `.env`:
```bash
# Example LLM Config (Groq, OpenAI, or Ollama)
LLM_API_KEY=your_key_here
LLM_PROVIDER=openai
LLM_MODEL=llama-3.3-70b-versatile
LLM_BASE_URL=https://api.groq.com/openai/v1

# Voice Synthesis
ELEVENLABS_API_KEY=your_key
```

## Running Development Chat
You can test the Agent Tool Loop interactively without triggering the audio pipeline by running:
```bash
uv run prysm chat
```