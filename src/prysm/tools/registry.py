
from prysm.tools.interfaces import Tool


class ToolRegistry:
    """Registry to manage and look up tools."""
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a new tool."""
        self._tools[tool.schema.name] = tool

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool by name."""
        self._tools.pop(tool_name, None)

    def get_tool(self, tool_name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(tool_name)

    def get_all_schemas(self) -> list[dict]:
        """Get schemas for all registered tools."""
        return [tool.schema.model_dump() for tool in self._tools.values()]
