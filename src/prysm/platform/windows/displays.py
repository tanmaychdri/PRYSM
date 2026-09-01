import ctypes
import ctypes.wintypes
import logging
from typing import Any

logger = logging.getLogger(__name__)

user32 = ctypes.windll.user32
MONITORENUMPROC = ctypes.WINFUNCTYPE(
    ctypes.wintypes.BOOL,
    ctypes.wintypes.HMONITOR,
    ctypes.wintypes.HDC,
    ctypes.POINTER(ctypes.wintypes.RECT),
    ctypes.wintypes.LPARAM,
)


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.wintypes.DWORD),
        ("rcMonitor", ctypes.wintypes.RECT),
        ("rcWork", ctypes.wintypes.RECT),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("szDevice", ctypes.c_wchar * 32),
    ]


class WindowsDisplayService:
    """Service for querying monitor topology."""

    def __init__(self):
        pass

    def list_displays(self) -> list[dict[str, Any]]:
        monitors = []

        def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
            mi = MONITORINFOEXW()
            mi.cbSize = ctypes.sizeof(MONITORINFOEXW)
            if user32.GetMonitorInfoW(hMonitor, ctypes.byref(mi)):
                is_primary = (mi.dwFlags & 1) != 0
                rect = mi.rcMonitor
                work = mi.rcWork
                monitors.append(
                    {
                        "id": mi.szDevice,
                        "is_primary": is_primary,
                        "rect": {
                            "left": rect.left,
                            "top": rect.top,
                            "right": rect.right,
                            "bottom": rect.bottom,
                            "width": rect.right - rect.left,
                            "height": rect.bottom - rect.top,
                        },
                        "work_area": {
                            "left": work.left,
                            "top": work.top,
                            "right": work.right,
                            "bottom": work.bottom,
                            "width": work.right - work.left,
                            "height": work.bottom - work.top,
                        },
                    }
                )
            return True

        user32.EnumDisplayMonitors(0, 0, MONITORENUMPROC(callback), 0)
        return monitors
