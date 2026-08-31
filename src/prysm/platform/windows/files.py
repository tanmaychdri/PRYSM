import logging
import os
from pathlib import Path
from typing import Any, Protocol

try:
    import winshell

    WINSHELL_AVAILABLE = True
except ImportError:
    WINSHELL_AVAILABLE = False

logger = logging.getLogger(__name__)


class FileController(Protocol):
    async def empty_recycle_bin(self) -> bool: ...
    async def search_files(
        self,
        query: str,
        directory: str,
        extension: str | None = None,
        max_results: int = 20,
    ) -> list[dict[str, Any]]: ...


class WindowsFileController:
    """Windows implementation of the FileController."""

    ALLOWED_SEARCH_ROOTS = [
        str(Path.home() / "Documents"),
        str(Path.home() / "Downloads"),
        str(Path.home() / "Desktop"),
        str(Path.home() / "Pictures"),
        str(Path.home() / "Music"),
        str(Path.home() / "Videos"),
        "C:\\PRYSM",  # Include PRYSM dir for dev
    ]

    async def empty_recycle_bin(self) -> bool:
        if not WINSHELL_AVAILABLE:
            logger.error("winshell not available for recycle bin operations.")
            return False

        try:
            logger.info("Emptying recycle bin")
            # confirm=False means it skips the OS dialog prompt
            # show_progress=False means it doesn't show the progress bar dialog
            # sound=False skips the crunch sound
            winshell.recycle_bin().empty(
                confirm=False, show_progress=False, sound=False
            )
            return True
        except Exception as e:
            logger.error(f"Failed to empty recycle bin: {e}")
            return False

    async def search_files(
        self,
        query: str,
        directory: str,
        extension: str | None = None,
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        query = query.lower()
        if extension and not extension.startswith("."):
            extension = f".{extension}"

        search_dir = Path(directory).resolve()

        # Security Check: Ensure search_dir is within an allowed root
        is_allowed = False
        for root in self.ALLOWED_SEARCH_ROOTS:
            try:
                root_path = Path(root).resolve()
                if search_dir == root_path or root_path in search_dir.parents:
                    is_allowed = True
                    break
            except Exception:
                continue

        if not is_allowed:
            raise PermissionError(
                f"Directory {directory} is outside allowed search roots."
            )

        results = []
        try:
            for root, _, files in os.walk(search_dir):
                if len(results) >= max_results:
                    break
                for file in files:
                    if len(results) >= max_results:
                        break

                    if extension and not file.endswith(extension):
                        continue

                    if query in file.lower():
                        full_path = Path(root) / file
                        results.append(
                            {
                                "name": file,
                                "path": str(full_path),
                                "size_bytes": full_path.stat().st_size,
                            }
                        )
        except Exception as e:
            logger.error(f"Error during file search: {e}")

        return results
