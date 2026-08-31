import platform
import sys
from datetime import datetime
from typing import Any

from prysm.os_integration.interfaces import SystemControl
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class SystemTimeGetTool(Tool):
    """Tool to get the current system time."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.time.get",
            description="Get the current system time and timezone.",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        now = datetime.now().astimezone()
        return {
            "local_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": str(now.tzinfo),
        }


class SystemInfoTool(Tool):
    """Tool to get basic system information."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.system_info",
            description="Get basic OS and hardware information about the system PRYSM is running on.",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        return {
            "os": platform.system(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "python_version": sys.version.split(" ")[0],
        }


class SystemVolumeGetTool(Tool):
    """Tool to get the system volume."""

    def __init__(self, sys_ctrl: SystemControl):
        self.sys_ctrl = sys_ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.volume.get",
            description="Get the current system volume level (0-100).",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        return {"level": self.sys_ctrl.get_volume()}


class SystemVolumeSetTool(Tool):
    """Tool to set the system volume."""

    def __init__(self, sys_ctrl: SystemControl):
        self.sys_ctrl = sys_ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.volume.set",
            description="Set the system volume to a specific level between 0 and 100.",
            parameters={
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "Volume level from 0 to 100.",
                        "minimum": 0,
                        "maximum": 100,
                    }
                },
                "required": ["level"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.LOW_RISK

    async def execute(self, **kwargs: Any) -> Any:
        level = kwargs.get("level")
        if not isinstance(level, int) or level < 0 or level > 100:
            raise ValueError("Volume level must be an integer between 0 and 100.")
        
        self.sys_ctrl.set_volume(level)
        return {"success": True, "level": level}


class SystemAppLaunchTool(Tool):
    """Tool to launch a whitelisted application."""

    def __init__(self, sys_ctrl: SystemControl):
        self.sys_ctrl = sys_ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.app.launch",
            description="Launch a known application (e.g., 'spotify', 'calculator', 'notepad').",
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The name of the application to launch (e.g., 'spotify', 'notepad').",
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
        
        success = self.sys_ctrl.launch_app(app_name)
        if not success:
            raise RuntimeError(f"Failed to launch '{app_name}' or it is not an allowed application.")
            
        return {"success": True, "app": app_name}
