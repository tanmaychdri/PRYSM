# PRYSM Architecture
PRYSM is built around an async, event-driven core. The `PrysmAssistant` manages state and orchestrates interactions across modules using an `EventBus`.

## Core Components
- **Core**: Events, state, lifecycle management.
- **Brain**: LLM interactions.
- **Audio**: Wake word, STT, TTS.
- **Memory**: Context persistence.
- **Vision**: Image analysis.
