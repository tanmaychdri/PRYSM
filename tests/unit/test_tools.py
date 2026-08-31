from typing import Any

from prysm.tools.interfaces import Tool, ToolSchema
from prysm.tools.registry import ToolRegistry


class DummyTool(Tool):
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(name="dummy", description="A dummy tool", parameters={})

    async def execute(self, **kwargs: Any) -> Any:
        return "dummy result"


def test_tool_registry():
    registry = ToolRegistry()
    tool = DummyTool()

    registry.register(tool)
    assert registry.get_tool("dummy") is tool

    schemas = registry.get_all_schemas()
    assert len(schemas) == 1
    assert schemas[0]["name"] == "dummy"

    registry.unregister("dummy")
    assert registry.get_tool("dummy") is None
