import json
import logging
from pathlib import Path

from prysm.platform.windows.applications import WindowsApplicationService
from prysm.platform.windows.windows import WindowsWindowService

logger = logging.getLogger(__name__)


class WindowsWorkspaceService:
    """Service for saving and restoring window arrangements (workspaces)."""

    def __init__(
        self, app_service: WindowsApplicationService, win_service: WindowsWindowService
    ):
        self.app_service = app_service
        self.win_service = win_service
        self.workspace_file = Path("data/workspaces.json")
        self.workspace_file.parent.mkdir(parents=True, exist_ok=True)
        self._workspaces = {}
        self._load_from_disk()

    def _load_from_disk(self):
        if self.workspace_file.exists():
            try:
                with open(self.workspace_file) as f:
                    self._workspaces = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load workspaces: {e}")

    def _save_to_disk(self):
        try:
            with open(self.workspace_file, "w") as f:
                json.dump(self._workspaces, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save workspaces: {e}")

    def list_workspaces(self) -> list[str]:
        return list(self._workspaces.keys())

    def save_workspace(self, name: str):
        windows = self.win_service.list_windows()
        # Filter out unimportant windows or background tasks if needed
        # For simplicity, we save all visible windows with titles

        apps = []
        for w in windows:
            # Try to resolve app name from process id or just save the title
            # In a real app we'd map PID -> Exe -> App Name
            apps.append({"title": w["title"], "pid": w["pid"], "rect": w["rect"]})

        self._workspaces[name] = apps
        self._save_to_disk()
        return True

    async def load_workspace(self, name: str) -> bool:
        if name not in self._workspaces:
            return False

        apps = self._workspaces[name]
        logger.info(f"Loading workspace {name} with {len(apps)} windows.")

        # Extremely simplified load: we don't know the executables here just from title,
        # but if we saved them, we would launch them.
        # For now, we just try to move existing windows that match the title.
        for app in apps:
            w = self.win_service.find_window(app["title"])
            if w:
                rect = app["rect"]
                self.win_service.restore_window(w["hwnd"])
                self.win_service.move_window(
                    w["hwnd"], rect["left"], rect["top"], rect["width"], rect["height"]
                )

        return True

    def delete_workspace(self, name: str) -> bool:
        if name in self._workspaces:
            del self._workspaces[name]
            self._save_to_disk()
            return True
        return False
