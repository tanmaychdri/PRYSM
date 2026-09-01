import asyncio
from typing import Any

from prysm.platform.windows.windows import WindowsWindowService
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class WindowListTool(Tool):
    def __init__(self, service: WindowsWindowService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="window.list",
            description="List all currently open and visible windows.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        return {"windows": self.service.list_windows()}


class WindowFindTool(Tool):
    def __init__(self, service: WindowsWindowService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="window.find",
            description="Find a specific window by its title or process ID.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Window title substring or PID.",
                    }
                },
                "required": ["query"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        return {"window": self.service.find_window(str(kwargs.get("query")))}


class WindowFocusTool(Tool):
    def __init__(self, service: WindowsWindowService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="window.focus",
            description="Bring a specific window to the foreground using its HWND.",
            parameters={
                "type": "object",
                "properties": {
                    "hwnd": {
                        "type": "integer",
                        "description": "The HWND of the window.",
                    }
                },
                "required": ["hwnd"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.LOW_RISK

    async def execute(self, **kwargs: Any) -> Any:
        success = self.service.focus_window(int(kwargs.get("hwnd", 0)))
        return {"success": success}


class WindowMoveTool(Tool):
    def __init__(self, service: WindowsWindowService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="window.move",
            description="Move and resize a window to specific coordinates.",
            parameters={
                "type": "object",
                "properties": {
                    "hwnd": {"type": "integer"},
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                },
                "required": ["hwnd", "x", "y", "width", "height"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.LOW_RISK

    async def execute(self, **kwargs: Any) -> Any:
        success = self.service.move_window(
            int(kwargs.get("hwnd", 0)),
            int(kwargs.get("x", 0)),
            int(kwargs.get("y", 0)),
            int(kwargs.get("width", 800)),
            int(kwargs.get("height", 600)),
        )
        return {"success": success}


class WindowWaitTool(Tool):
    def __init__(self, service: WindowsWindowService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="window.wait",
            description="Wait for a window with a specific title to appear. Use this after launching an app.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Title substring"},
                    "timeout": {
                        "type": "integer",
                        "description": "Seconds to wait (default 10)",
                    },
                },
                "required": ["query"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        query = str(kwargs.get("query"))
        timeout = int(kwargs.get("timeout", 10))

        for _ in range(timeout * 2):
            w = self.service.find_window(query)
            if w:
                return {"success": True, "window": w}
            await asyncio.sleep(0.5)

        return {"success": False, "error": "Timed out waiting for window."}


class OsWindowTools:
    def __init__(self, service: WindowsWindowService):
        self.service = service

    def register(self, registry):
        registry.register(WindowListTool(self.service))
        registry.register(WindowFindTool(self.service))
        registry.register(WindowFocusTool(self.service))
        registry.register(WindowMoveTool(self.service))
        registry.register(WindowWaitTool(self.service))
