from typing import Any

from prysm.mobile.service import MobileService
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class MobileDeviceListTool(Tool):
    def __init__(self, service: MobileService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="mobile.device.list",
            description="List all paired Android devices and their IDs.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        devices = self.service.registry.get_all_devices()
        return [
            {
                "device_id": dev.device_id,
                "name": dev.name,
                "platform": dev.platform,
                "capabilities": dev.capabilities,
                "is_connected": dev.device_id in self.service.get_connected_devices(),
            }
            for dev in devices
        ]


class MobileDeviceStatusTool(Tool):
    def __init__(self, service: MobileService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="mobile.device.status",
            description="Get the connection status and battery/network info of a specific mobile device.",
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
            device_id, "mobile.device.status", {}
        )


class MobileDeviceRevokeTool(Tool):
    def __init__(self, service: MobileService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="mobile.device.revoke",
            description="Revoke access to a paired Android device, forcing it to pair again.",
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
        return ToolRisk.HIGH_RISK

    async def execute(self, **kwargs: Any) -> Any:
        device_id = kwargs.get("device_id")
        if device_id in self.service.get_connected_devices():
            try:
                ws = self.service.server.active_connections.get(device_id)
                if ws:
                    await ws.close()
            except Exception:
                pass
        self.service.registry.remove_device(device_id)
        return {"success": True, "message": f"Device {device_id} has been revoked."}


class MobileDeviceTools:
    def __init__(self, service: MobileService):
        self.service = service

    def register(self, registry):
        registry.register(MobileDeviceListTool(self.service))
        registry.register(MobileDeviceStatusTool(self.service))
        registry.register(MobileDeviceRevokeTool(self.service))

    # Provide these so the CLI can use them directly without mock args
    async def revoke_device(self, device_id: str):
        return await MobileDeviceRevokeTool(self.service).execute(device_id=device_id)

    async def device_status(self, device_id: str):
        return await MobileDeviceStatusTool(self.service).execute(device_id=device_id)
