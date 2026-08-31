from typing import Any

from prysm.tools.interfaces import Tool, ToolSchema


class EchoTool(Tool):
    """A mock tool that echoes input for testing."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="echo_tool",
            description="Echoes the provided message.",
            parameters={
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
            },
        )

    async def execute(self, message: str, **kwargs: Any) -> Any:
        return f"Echo: {message}"
