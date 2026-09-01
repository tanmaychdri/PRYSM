from typing import Any

from prysm.platform.windows.displays import WindowsDisplayService
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class DisplayListTool(Tool):
    def __init__(self, service: WindowsDisplayService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="display.list",
            description="List all connected monitors and their resolutions/coordinates.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        return {"displays": self.service.list_displays()}


class OsDisplayTools:
    def __init__(self, service: WindowsDisplayService):
        self.service = service

    def register(self, registry):
        registry.register(DisplayListTool(self.service))
