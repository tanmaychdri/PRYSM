from typing import Any

from prysm.mobile.service import MobileService
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class MobileLocationGetTool(Tool):
    def __init__(self, service: MobileService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="mobile.location.get",
            description="Get the current GPS location of the paired Android device.",
            parameters={
                "type": "object",
                "properties": {
                    "device_id": {
                        "type": "string",
                        "description": "The unique ID of the paired device.",
                    }
                },
                "required": ["device_id"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        device_id = kwargs.get("device_id")
        return await self.service.send_device_request(
            device_id, "mobile.location.get", {}
        )


class MobileLocationTools:
    def __init__(self, service: MobileService):
        self.service = service

    def register(self, registry):
        registry.register(MobileLocationGetTool(self.service))
