import logging
import subprocess
from prysm.os_integration.interfaces import SystemControl

logger = logging.getLogger(__name__)


class WindowsSystemControl(SystemControl):
    """Windows-specific OS control."""

    def __init__(self):
        # Fake volume state for Phase 4 testing (Windows audio APIs via ctypes are too complex for a thin layer)
        self._mock_volume = 50
        
        self.APP_MAP = {
            "spotify": "spotify.exe",
            "calculator": "calc.exe",
            "notepad": "notepad.exe",
        }

    def get_volume(self) -> int:
        return self._mock_volume

    def set_volume(self, level: int) -> None:
        self._mock_volume = max(0, min(100, level))
        logger.info(f"[WindowsSystemControl] Mock volume set to {self._mock_volume}%")

    def launch_app(self, app_name: str) -> bool:
        normalized_name = app_name.lower().strip()
        exe = self.APP_MAP.get(normalized_name)
        
        if not exe:
            logger.warning(f"[WindowsSystemControl] App '{app_name}' not found in registry.")
            return False
            
        try:
            logger.info(f"[WindowsSystemControl] Launching {exe}")
            subprocess.Popen(["start", exe], shell=True)
            return True
        except Exception as e:
            logger.error(f"[WindowsSystemControl] Failed to launch {exe}: {e}")
            return False
