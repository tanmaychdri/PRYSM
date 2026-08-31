from typing import Any

from prysm.mobile.service import MobileService
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class MobileSmsSendTool(Tool):
    def __init__(self, service: MobileService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="mobile.sms.send",
            description="Send an SMS message from the paired Android device.",
            parameters={
                "type": "object",
                "properties": {
                    "device_id": {
                        "type": "string",
                        "description": "The unique ID of the paired device."
                    },
                    "recipient": {
                        "type": "string",
                        "description": "The phone number or resolved contact to send the SMS to."
                    },
                    "message": {
                        "type": "string",
                        "description": "The body of the SMS message."
                    }
                },
                "required": ["device_id", "recipient", "message"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.HIGH_RISK

    async def execute(self, **kwargs: Any) -> Any:
        device_id = kwargs.get("device_id")
        recipient = kwargs.get("recipient")
        message = kwargs.get("message")
        return await self.service.send_device_request(
            device_id, 
            "mobile.sms.send", 
            {"to": recipient, "body": message}
        )

class MobileSmsListTool(Tool):
    def __init__(self, service: MobileService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="mobile.sms.list",
            description="List recent SMS conversations from the paired Android device.",
            parameters={
                "type": "object",
                "properties": {
                    "device_id": {
                        "type": "string",
                        "description": "The unique ID of the paired device."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of recent conversations to fetch (default 10)."
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
        limit = kwargs.get("limit", 10)
        return await self.service.send_device_request(
            device_id, 
            "mobile.sms.list", 
            {"limit": limit}
        )

class MobileSmsTools:
    def __init__(self, service: MobileService):
        self.service = service

    def register(self, registry):
        registry.register(MobileSmsSendTool(self.service))
        registry.register(MobileSmsListTool(self.service))
