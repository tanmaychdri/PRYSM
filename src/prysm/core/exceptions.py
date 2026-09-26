class PrysmError(Exception):
    """Base exception for all PRYSM errors."""


class InvalidStateTransitionError(PrysmError):
    """Raised when an invalid assistant state transition is attempted."""


class ToolNotFoundError(PrysmError):
    """Raised when a requested tool is not registered."""


class LLMError(PrysmError):
    """Raised when the LLM provider fails."""


class STTError(PrysmError):
    """Raised when speech-to-text fails."""


class TTSError(PrysmError):
    """Raised when text-to-speech fails."""


class AudioError(PrysmError):
    """Raised for audio capture/playback errors."""
