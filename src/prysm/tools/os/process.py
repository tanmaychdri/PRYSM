from typing import Any

from prysm.platform.windows.processes import WindowsProcessController
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class ProcessListTool(Tool):
    def __init__(self, ctrl: WindowsProcessController):
        self.ctrl = ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="process.list",
            description="List the top running processes sorted by memory usage.",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of processes to return (default 20).",
                    }
                },
                "required": [],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        limit = kwargs.get("limit", 20)
        return {"processes": await self.ctrl.list_processes(limit=limit)}


class ProcessFindTool(Tool):
    def __init__(self, ctrl: WindowsProcessController):
        self.ctrl = ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="process.find",
            description="Find a process by PID.",
            parameters={
                "type": "object",
                "properties": {"pid": {"type": "integer", "description": "Process ID"}},
                "required": ["pid"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        pid = kwargs.get("pid")
        if not pid:
            raise ValueError("PID is required")
        proc = await self.ctrl.get_process(pid)
        if proc:
            return {"process": proc}
        return {"error": "Process not found"}


class ProcessKillTool(Tool):
    def __init__(self, ctrl: WindowsProcessController):
        self.ctrl = ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="process.kill",
            description="Terminate a process by its PID.",
            parameters={
                "type": "object",
                "properties": {
                    "pid": {"type": "integer", "description": "Process ID to kill."}
                },
                "required": ["pid"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.HIGH_RISK

    async def execute(self, **kwargs: Any) -> Any:
        pid = kwargs.get("pid")
        if not pid:
            raise ValueError("PID is required")
        success = await self.ctrl.kill_process(pid)
        return {"success": success}


class OsProcessTools:
    def __init__(self, ctrl: WindowsProcessController):
        self.ctrl = ctrl

    def register(self, registry):
        registry.register(ProcessListTool(self.ctrl))
        registry.register(ProcessFindTool(self.ctrl))
        registry.register(ProcessKillTool(self.ctrl))
