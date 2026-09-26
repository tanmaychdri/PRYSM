import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from prysm.tools.interfaces import BaseTool

from prysm.core.exceptions import ToolNotFoundError

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry mapping tool names to their schemas and handlers."""

    def __init__(self) -> None:
        self._schemas: dict[str, dict[str, Any]] = {}
        self._handlers: dict[str, "BaseTool"] = {}

    def register(self, name: str, schema: dict[str, Any], handler: "BaseTool") -> None:
        if name in self._schemas:
            logger.warning(f"Tool '{name}' is already registered — overwriting")
        self._schemas[name] = schema
        self._handlers[name] = handler
        logger.debug(f"Registered tool: {name}")

    def get_schema(self, name: str) -> dict[str, Any]:
        if name not in self._schemas:
            raise ToolNotFoundError(f"Tool '{name}' not found")
        return self._schemas[name]

    def get_handler(self, name: str) -> "BaseTool":
        if name not in self._handlers:
            raise ToolNotFoundError(f"Tool '{name}' not found")
        return self._handlers[name]

    def get_all_schemas(self) -> list[dict[str, Any]]:
        return list(self._schemas.values())

    def list_tools(self) -> list[str]:
        return list(self._schemas.keys())
