from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Base class for all PRYSM tools."""

    @abstractmethod
    def get_schemas(self) -> list[dict[str, Any]]:
        """Return a list of OpenAI-compatible function schemas for this tool group."""
        ...

    @abstractmethod
    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute a named tool with the given arguments."""
        ...

    def register(self, registry: "ToolRegistry") -> None:  # type: ignore[name-defined]
        from prysm.tools.registry import ToolRegistry
        for schema in self.get_schemas():
            registry.register(schema["name"], schema, self)
