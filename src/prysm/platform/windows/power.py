import logging
import subprocess
from typing import Protocol

logger = logging.getLogger(__name__)


class PowerController(Protocol):
    async def sleep(self) -> bool: ...
    async def restart(self) -> bool: ...
    async def shutdown(self) -> bool: ...
    async def lock_screen(self) -> bool: ...


class WindowsPowerController:
    """Windows implementation of the PowerController."""

    async def sleep(self) -> bool:
        try:
            logger.info("Suspending Windows (Sleep)")
            subprocess.run(
                ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to sleep: {e}")
            return False

    async def restart(self) -> bool:
        try:
            logger.info("Restarting Windows")
            subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to restart: {e}")
            return False

    async def shutdown(self) -> bool:
        try:
            logger.info("Shutting down Windows")
            subprocess.run(["shutdown", "/s", "/t", "0"], check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to shutdown: {e}")
            return False

    async def lock_screen(self) -> bool:
        try:
            logger.info("Locking Windows Screen")
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to lock screen: {e}")
            return False
