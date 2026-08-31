import logging
import subprocess
from typing import Protocol

import psutil

logger = logging.getLogger(__name__)


class ApplicationController(Protocol):
    async def launch_app(self, app_name: str) -> bool: ...
    async def close_app(self, app_name: str) -> bool: ...


class WindowsApplicationController:
    """Windows implementation of the ApplicationController."""

    def __init__(self):
        # Default application registry mapping logical names to executable names or paths
        self.APP_REGISTRY = {
            "spotify": "spotify.exe",
            "calculator": "calc.exe",
            "notepad": "notepad.exe",
            "explorer": "explorer.exe",
            "cmd": "cmd.exe",
            "vscode": "code.cmd",
            "chrome": "chrome.exe",
            "edge": "msedge.exe",
            "settings": "ms-settings:",
        }

    async def launch_app(self, app_name: str) -> bool:
        normalized_name = app_name.lower().strip()
        exe = self.APP_REGISTRY.get(normalized_name)

        if not exe:
            logger.warning(f"App '{app_name}' not found in Application Registry.")
            raise ValueError(f"Application '{app_name}' is not registered.")

        try:
            logger.info(f"Launching {exe}")
            if exe.startswith("ms-"):
                subprocess.Popen(["start", exe], shell=True)
            else:
                subprocess.Popen(["start", "", exe], shell=True)
            return True
        except Exception as e:
            logger.error(f"Failed to launch app {app_name}: {e}")
            return False

    async def close_app(self, app_name: str) -> bool:
        normalized_name = app_name.lower().strip()
        exe = self.APP_REGISTRY.get(normalized_name)

        if not exe:
            logger.warning(f"App '{app_name}' not found in Application Registry.")
            raise ValueError(f"Application '{app_name}' is not registered.")

        if exe.startswith("ms-"):
            logger.warning(f"Cannot reliably close UWP/URI apps like '{app_name}'")
            return False

        try:
            killed = False
            for proc in psutil.process_iter(["name"]):
                if proc.info["name"] and proc.info["name"].lower() == exe.lower():
                    proc.terminate()
                    killed = True

            return killed
        except Exception as e:
            logger.error(f"Failed to close app {app_name}: {e}")
            return False
