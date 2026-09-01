import datetime
from typing import Any

from prysm.platform.windows.system import WindowsSystemService
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema

class SystemTimeGetTool(Tool):
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.time.get",
            description="Get the current system time and date.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        now = datetime.datetime.now()
        return {
            "current_time": now.isoformat(),
            "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
        }


class SystemInfoTool(Tool):
    def __init__(self, service: WindowsSystemService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.info",
            description="Get general information about the PC (OS, CPU, RAM total, Uptime).",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        return self.service.get_system_info()


class SystemMetricsTool(Tool):
    def __init__(self, service: WindowsSystemService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.metrics",
            description="Get current CPU, RAM, and Disk usage percentages.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        return self.service.get_metrics()


class ClipboardGetTool(Tool):
    def __init__(self, service: WindowsSystemService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="clipboard.get",
            description="Get the current text from the Windows clipboard.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        return {"clipboard": self.service.get_clipboard()}


class ClipboardSetTool(Tool):
    def __init__(self, service: WindowsSystemService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="clipboard.set",
            description="Set the Windows clipboard to a specific string.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to put in the clipboard.",
                    }
                },
                "required": ["text"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.LOW_RISK

    async def execute(self, **kwargs: Any) -> Any:
        success = self.service.set_clipboard(str(kwargs.get("text", "")))
        return {"success": success}


class OsSystemTools:
    def __init__(self, service: WindowsSystemService):
        self.service = service

    def register(self, registry):
        registry.register(SystemInfoTool(self.service))
        registry.register(SystemMetricsTool(self.service))
        registry.register(ClipboardGetTool(self.service))
        registry.register(ClipboardSetTool(self.service))
        registry.register(SystemTimeGetTool())
