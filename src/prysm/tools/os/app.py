from typing import Any

from prysm.platform.windows.applications import WindowsApplicationService
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class AppListTool(Tool):
    def __init__(self, service: WindowsApplicationService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="app.list",
            description="List installed and known applications on this PC.",
            parameters={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": "Optional search string to filter apps.",
                    }
                },
                "required": [],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        return {"apps": self.service.list_installed_apps(kwargs.get("filter"))}


class AppLaunchTool(Tool):
    def __init__(self, service: WindowsApplicationService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="app.launch",
            description="Launch or open an application by its name.",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the app to launch (e.g. 'chrome', 'vscode', 'notepad').",
                    }
                },
                "required": ["name"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.LOW_RISK

    async def execute(self, **kwargs: Any) -> Any:
        success = await self.service.launch_app(str(kwargs.get("name")))
        return {"success": success}


class AppCloseTool(Tool):
    def __init__(self, service: WindowsApplicationService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="app.close",
            description="Close an application safely by sending termination signal.",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the app to close.",
                    }
                },
                "required": ["name"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.MEDIUM_RISK

    async def execute(self, **kwargs: Any) -> Any:
        success = await self.service.close_app(str(kwargs.get("name")), force=False)
        return {"success": success}


class AppForceCloseTool(Tool):
    def __init__(self, service: WindowsApplicationService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="app.force_close",
            description="Force kill an application if it is unresponsive.",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the app to force close.",
                    }
                },
                "required": ["name"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.HIGH_RISK

    async def execute(self, **kwargs: Any) -> Any:
        success = await self.service.close_app(str(kwargs.get("name")), force=True)
        return {"success": success}


class OsAppTools:
    def __init__(self, service: WindowsApplicationService):
        self.service = service

    def register(self, registry):
        registry.register(AppListTool(self.service))
        registry.register(AppLaunchTool(self.service))
        registry.register(AppCloseTool(self.service))
        registry.register(AppForceCloseTool(self.service))
