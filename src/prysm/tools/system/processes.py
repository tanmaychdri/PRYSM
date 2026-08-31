from typing import Any

from prysm.platform.windows.processes import ProcessController
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class SystemProcessListTool(Tool):
    def __init__(self, proc_ctrl: ProcessController):
        self.proc_ctrl = proc_ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.process.list",
            description="List the top running processes on the system, sorted by memory usage.",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of processes to return (default 50).",
                        "maximum": 100,
                    }
                },
                "required": [],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        limit = kwargs.get("limit", 50)
        return {"processes": await self.proc_ctrl.list_processes(limit=limit)}


class SystemProcessGetTool(Tool):
    def __init__(self, proc_ctrl: ProcessController):
        self.proc_ctrl = proc_ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.process.get",
            description="Get detailed information about a specific process by its PID.",
            parameters={
                "type": "object",
                "properties": {
                    "pid": {
                        "type": "integer",
                        "description": "Process ID.",
                    }
                },
                "required": ["pid"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        pid = kwargs.get("pid")
        if not pid:
            raise ValueError("pid is required.")

        info = await self.proc_ctrl.get_process(pid)
        if not info:
            raise RuntimeError(f"Process with PID {pid} not found.")

        return info


class SystemProcessKillTool(Tool):
    def __init__(self, proc_ctrl: ProcessController):
        self.proc_ctrl = proc_ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.process.kill",
            description="Kill a process by its PID. This is a high-risk operation.",
            parameters={
                "type": "object",
                "properties": {
                    "pid": {
                        "type": "integer",
                        "description": "Process ID to kill.",
                    }
                },
                "required": ["pid"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.HIGH_RISK

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> Any:
        pid = kwargs.get("pid")
        if not pid:
            raise ValueError("pid is required.")

        success = await self.proc_ctrl.kill_process(pid)
        if not success:
            raise RuntimeError(f"Failed to kill process {pid} or it was not found.")

        return {"success": True, "pid": pid}
