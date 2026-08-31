class PrysmError(Exception):
    """Base exception for all Prysm errors."""

    pass


class ConfigurationError(PrysmError):
    """Raised when there is a configuration error."""

    pass


class InitializationError(PrysmError):
    """Raised when an initialization error occurs."""

    pass
