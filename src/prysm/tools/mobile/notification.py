from typing import Any

from prysm.mobile.service import MobileService
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class MobileNotificationListTool(Tool):
    def __init__(self, service: MobileService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="mobile.notification.list",
            description="List recent notifications from the paired Android device.",
            parameters={
                "type": "object",
                "properties": {
                    "device_id": {
                        "type": "string",
                        "description": "The unique ID of the paired device.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of recent notifications to fetch.",
                    },
                    "package_filter": {
                        "type": "string",
                        "description": "Optional package or app name to filter by.",
                    },
                },
                "required": ["device_id"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        device_id = kwargs.get("device_id")
        limit = kwargs.get("limit", 20)
        package_filter = kwargs.get("package_filter", "")
        return await self.service.send_device_request(
            device_id,
            "mobile.notification.list",
            {"limit": limit, "package_filter": package_filter},
        )


class MobileNotificationTools:
    def __init__(self, service: MobileService):
        self.service = service

    def register(self, registry):
        registry.register(MobileNotificationListTool(self.service))
