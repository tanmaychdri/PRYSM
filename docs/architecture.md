# PRYSM Architecture
PRYSM is built around an async, event-driven core. The `PrysmAssistant` manages state and orchestrates interactions across modules using an `EventBus`.

## Conceptual Flow
```text
Input
 ↓
RequestContext
 ↓
Assistant Core
 ↓
State Manager
 ↓
Brain Provider
 ↓
BrainResponse
 ↓
Response
```

## Core Components
- **Core**: Events, state, lifecycle management, request context.
- **Brain**: LLM interactions (Mock provider currently).
- **Audio**: Wake word, STT, TTS (Not yet implemented).
- **Memory**: Context persistence (Not yet implemented).
- **Vision**: Image analysis (Not yet implemented).
- **Tools**: Tool Registry and execution (Not yet implemented).
- **Integrations**: UI and Mobile (Not yet implemented).
