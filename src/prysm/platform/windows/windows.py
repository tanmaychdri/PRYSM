import ctypes
import ctypes.wintypes
import logging
from typing import Any

logger = logging.getLogger(__name__)

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(
    ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM
)

SW_RESTORE = 9
SW_MINIMIZE = 6
SW_MAXIMIZE = 3


class WindowsWindowService:
    """Service for managing Windows UI windows via user32."""

    def __init__(self):
        pass

    def _get_window_title(self, hwnd) -> str:
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return ""
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value

    def _is_visible(self, hwnd) -> bool:
        return user32.IsWindowVisible(hwnd) != 0

    def list_windows(self) -> list[dict[str, Any]]:
        windows = []

        def callback(hwnd, lParam):
            if self._is_visible(hwnd):
                title = self._get_window_title(hwnd)
                if title:  # Only windows with titles
                    pid = ctypes.wintypes.DWORD()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

                    # Get rect
                    rect = ctypes.wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(rect))

                    windows.append(
                        {
                            "hwnd": hwnd,
                            "title": title,
                            "pid": pid.value,
                            "rect": {
                                "left": rect.left,
                                "top": rect.top,
                                "right": rect.right,
                                "bottom": rect.bottom,
                                "width": rect.right - rect.left,
                                "height": rect.bottom - rect.top,
                            },
                        }
                    )
            return True

        user32.EnumWindows(WNDENUMPROC(callback), 0)
        return windows

    def find_window(self, query: str) -> dict[str, Any] | None:
        """Find a window by title (substring) or PID (if query is digit)."""
        query_lower = query.lower()
        windows = self.list_windows()

        # Try PID exact match if digit
        if query.isdigit():
            pid = int(query)
            for w in windows:
                if w["pid"] == pid:
                    return w

        # Try title match
        for w in windows:
            if query_lower in w["title"].lower():
                return w

        return None

    def focus_window(self, hwnd: int) -> bool:
        user32.ShowWindow(hwnd, SW_RESTORE)
        return user32.SetForegroundWindow(hwnd) != 0

    def move_window(self, hwnd: int, x: int, y: int, width: int, height: int) -> bool:
        # HWND_TOP = 0, SWP_SHOWWINDOW = 0x0040
        return user32.SetWindowPos(hwnd, 0, x, y, width, height, 0x0040) != 0

    def minimize_window(self, hwnd: int) -> bool:
        return user32.ShowWindow(hwnd, SW_MINIMIZE) != 0

    def maximize_window(self, hwnd: int) -> bool:
        return user32.ShowWindow(hwnd, SW_MAXIMIZE) != 0

    def restore_window(self, hwnd: int) -> bool:
        return user32.ShowWindow(hwnd, SW_RESTORE) != 0

    def close_window(self, hwnd: int) -> bool:
        WM_CLOSE = 0x0010
        return user32.PostMessageW(hwnd, WM_CLOSE, 0, 0) != 0
