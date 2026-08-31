from enum import Enum, auto


class AssistantState(Enum):
    """Enum representing the core state of the assistant."""
    STARTING = auto()
    IDLE = auto()
    LISTENING = auto()
    THINKING = auto()
    SPEAKING = auto()
    ERROR = auto()
    STOPPING = auto()
