import platform
import sys
from datetime import datetime
from typing import Any

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
