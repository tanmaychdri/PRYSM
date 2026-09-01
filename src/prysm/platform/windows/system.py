import logging
import platform
import subprocess
from datetime import UTC, datetime
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class WindowsSystemService:
    """Service for system metrics and clipboard."""

    def __init__(self):
        pass

    def get_system_info(self) -> dict[str, Any]:
        uname = platform.uname()
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        boot_time = datetime.fromtimestamp(psutil.boot_time(), UTC)

        return {
            "os": f"{uname.system} {uname.release}",
            "version": uname.version,
            "machine": uname.machine,
            "processor": uname.processor,
            "cpu_cores_physical": psutil.cpu_count(logical=False),
            "cpu_cores_logical": psutil.cpu_count(logical=True),
            "ram_total_gb": round(mem.total / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "boot_time": boot_time.isoformat(),
            "uptime_hours": round(
                (datetime.now(UTC) - boot_time).total_seconds() / 3600, 2
            ),
        }

    def get_metrics(self) -> dict[str, Any]:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "ram_percent": mem.percent,
            "ram_used_gb": round(mem.used / (1024**3), 2),
            "disk_percent": disk.percent,
        }

    def get_clipboard(self) -> str:
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get clipboard: {e}")
            return ""

    def set_clipboard(self, text: str) -> bool:
        try:
            process = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value $input"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            process.communicate(input=text, timeout=3)
            return process.returncode == 0
        except Exception as e:
            logger.error(f"Failed to set clipboard: {e}")
            return False
