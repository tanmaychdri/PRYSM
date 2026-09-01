import logging
import os
import subprocess
from pathlib import Path

import psutil

logger = logging.getLogger(__name__)


class WindowsApplicationService:
    """Service for discovering, launching, and terminating Windows applications."""

    def __init__(self):
        self._app_cache: dict[str, str] = {}
        self._scan_completed = False

        # Static aliases and fallback apps that might not have a .lnk or where we prefer a specific command
        self.STATIC_APPS = {
            "calculator": "calc.exe",
            "notepad": "notepad.exe",
            "explorer": "explorer.exe",
            "cmd": "cmd.exe",
            "command prompt": "cmd.exe",
            "settings": "ms-settings:",
        }

    def _scan_apps(self):
        if self._scan_completed:
            return

        logger.info("Scanning for installed applications...")
        paths = [
            Path(os.environ.get("ALLUSERSPROFILE", "C:\\ProgramData"))
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs",
            Path(os.environ.get("APPDATA", ""))
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs",
        ]

        for p in paths:
            if not p.exists():
                continue
            for lnk in p.rglob("*.lnk"):
                name = lnk.stem.lower()
                # Skip common uninstaller links
                if "uninstall" in name:
                    continue
                self._app_cache[name] = str(lnk)

        self._scan_completed = True
        logger.info(f"Discovered {len(self._app_cache)} applications.")

    def _resolve_app(self, app_name: str) -> str | None:
        self._scan_apps()
        normalized_name = app_name.lower().strip()

        # 1. Check static overrides
        if normalized_name in self.STATIC_APPS:
            return self.STATIC_APPS[normalized_name]

        # 2. Exact match in cache
        if normalized_name in self._app_cache:
            return self._app_cache[normalized_name]

        # 3. Substring match (e.g. 'chrome' matches 'google chrome')
        for cached_name, path in self._app_cache.items():
            if normalized_name in cached_name:
                return path

        return None

    def list_installed_apps(self, filter_str: str | None = None) -> list[str]:
        self._scan_apps()
        all_apps = list(self.STATIC_APPS.keys()) + list(self._app_cache.keys())
        all_apps = list(set(all_apps))
        all_apps.sort()

        if filter_str:
            f = filter_str.lower()
            all_apps = [a for a in all_apps if f in a]

        return all_apps

    async def launch_app(self, app_name: str) -> bool:
        exe_or_path = self._resolve_app(app_name)

        if not exe_or_path:
            logger.warning(f"App '{app_name}' not found.")
            raise ValueError(f"Application '{app_name}' could not be found.")

        try:
            logger.info(f"Launching {exe_or_path}")
            if exe_or_path.startswith("ms-"):
                subprocess.Popen(["start", exe_or_path], shell=True)
            else:
                subprocess.Popen(["start", "", exe_or_path], shell=True)
            return True
        except Exception as e:
            logger.error(f"Failed to launch app {app_name}: {e}")
            raise RuntimeError(f"Failed to launch app: {e}")

    async def close_app(self, app_name: str, force: bool = False) -> bool:
        """
        Closes an app by matching its executable name or path.
        For exact closure, we need to match running processes.
        Since we might only have a .lnk file, we resolve it to the exe name roughly,
        or just kill based on a process name search.
        """
        normalized_name = app_name.lower().strip()

        # Try finding process by substring
        killed = False
        try:
            for proc in psutil.process_iter(["name", "exe"]):
                proc_name = (proc.info.get("name") or "").lower()
                # If the app name is 'chrome', it matches 'chrome.exe'
                if normalized_name in proc_name:
                    if force:
                        proc.kill()
                    else:
                        proc.terminate()
                    killed = True

            return killed
        except Exception as e:
            logger.error(f"Failed to close app {app_name}: {e}")
            raise RuntimeError(f"Failed to close app: {e}")
