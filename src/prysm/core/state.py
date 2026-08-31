from enum import Enum, auto


class AssistantState(Enum):
    """Enum representing the core state of the assistant."""

    STARTING = auto()
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    THINKING = auto()
    EXECUTING_TOOL = auto()
    RESPONDING = auto()
    SPEAKING = auto()
    ERROR = auto()
    STOPPING = auto()
    STOPPED = auto()
