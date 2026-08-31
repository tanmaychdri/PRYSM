import logging
from typing import Any, Protocol

import psutil

logger = logging.getLogger(__name__)


class ProcessController(Protocol):
    async def list_processes(self, limit: int = 50) -> list[dict[str, Any]]: ...
    async def get_process(self, pid: int) -> dict[str, Any] | None: ...
    async def kill_process(self, pid: int) -> bool: ...


class WindowsProcessController:
    """Windows implementation of the ProcessController using psutil."""

    PROTECTED_PROCESSES = {
        "explorer.exe",
        "svchost.exe",
        "winlogon.exe",
        "csrss.exe",
        "smss.exe",
        "services.exe",
        "lsass.exe",
        "dwm.exe",
        "taskmgr.exe",
        "system",
        "registry",
        "fontdrvhost.exe",
        "wininit.exe",
        "spoolsv.exe",
        "searchui.exe",
        "sihost.exe",
    }

    async def list_processes(self, limit: int = 50) -> list[dict[str, Any]]:
        processes = []
        try:
            # We want to iterate fast and avoid AccessDenied errors as much as possible
            for proc in psutil.process_iter(
                ["pid", "name", "cpu_percent", "memory_info"]
            ):
                try:
                    info = proc.info
                    processes.append(
                        {
                            "pid": info["pid"],
                            "name": info["name"],
                            "cpu_percent": info.get("cpu_percent", 0),
                            "memory_mb": getattr(info.get("memory_info"), "rss", 0)
                            / (1024 * 1024),
                        }
                    )
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    pass

            # Sort by memory usage descending and return top `limit`
            processes.sort(key=lambda p: p.get("memory_mb", 0), reverse=True)
            return processes[:limit]
        except Exception as e:
            logger.error(f"Failed to list processes: {e}")
            return []

    async def get_process(self, pid: int) -> dict[str, Any] | None:
        try:
            proc = psutil.Process(pid)
            return {
                "pid": proc.pid,
                "name": proc.name(),
                "status": proc.status(),
                "cpu_percent": proc.cpu_percent(),
                "memory_mb": proc.memory_info().rss / (1024 * 1024),
                "create_time": proc.create_time(),
            }
        except psutil.NoSuchProcess:
            return None
        except Exception as e:
            logger.error(f"Failed to get process {pid}: {e}")
            return None

    async def kill_process(self, pid: int) -> bool:
        try:
            proc = psutil.Process(pid)
            name = proc.name().lower()

            if name in self.PROTECTED_PROCESSES:
                logger.warning(f"Attempted to kill protected process: {name} ({pid})")
                raise RuntimeError(f"Cannot kill protected system process: {name}")

            proc.terminate()
            proc.wait(timeout=3)
            return True
        except psutil.NoSuchProcess:
            return False
        except psutil.TimeoutExpired:
            # Force kill if terminate hangs
            proc.kill()
            return True
        except Exception as e:
            logger.error(f"Failed to kill process {pid}: {e}")
            raise
