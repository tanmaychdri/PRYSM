from enum import auto, Enum


class AssistantState(Enum):
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
