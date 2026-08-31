from typing import Any

from prysm.platform.windows.applications import ApplicationController
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class SystemAppLaunchTool(Tool):
    def __init__(self, app_ctrl: ApplicationController):
        self.app_ctrl = app_ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.app.launch",
            description="Launch a known application (e.g., 'spotify', 'calculator', 'notepad', 'vscode', 'explorer').",
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The logical name of the application to launch.",
                    }
                },
                "required": ["app_name"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.LOW_RISK

    async def execute(self, **kwargs: Any) -> Any:
        app_name = kwargs.get("app_name")
        if not app_name:
            raise ValueError("app_name is required.")

        success = await self.app_ctrl.launch_app(app_name)
        if not success:
            raise RuntimeError(f"Failed to launch '{app_name}'.")

        return {"success": True, "app": app_name}


class SystemAppCloseTool(Tool):
    def __init__(self, app_ctrl: ApplicationController):
        self.app_ctrl = app_ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.app.close",
            description="Close a running application (e.g., 'spotify', 'notepad').",
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The logical name of the application to close.",
                    }
                },
                "required": ["app_name"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.HIGH_RISK

    @property
    def requires_confirmation(self) -> bool:
        # Closing apps shouldn't strictly require confirmation if it's explicitly asked,
        # but the prompt says high risk. We can require confirmation to be safe.
        return True

    async def execute(self, **kwargs: Any) -> Any:
        app_name = kwargs.get("app_name")
        if not app_name:
            raise ValueError("app_name is required.")

        success = await self.app_ctrl.close_app(app_name)
        if not success:
            raise RuntimeError(f"Failed to close '{app_name}' or it is not running.")

        return {"success": True, "app": app_name}
