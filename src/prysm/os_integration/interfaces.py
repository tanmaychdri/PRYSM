from abc import ABC, abstractmethod


class SystemControl(ABC):
    """Abstract interface for OS-level control."""

    @abstractmethod
    def get_volume(self) -> int:
        """Get the current system volume (0-100)."""
        pass

    @abstractmethod
    def set_volume(self, level: int) -> None:
        """Set the system volume (0-100)."""
        pass

    @abstractmethod
    def launch_app(self, app_name: str) -> bool:
        """Launch a known application by its friendly name."""
        pass
