from typing import Any

from prysm.platform.windows.power import WindowsPowerController
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class PowerSleepTool(Tool):
    def __init__(self, ctrl: WindowsPowerController):
        self.ctrl = ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="power.sleep",
            description="Put the system to sleep (suspend).",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.HIGH_RISK

    async def execute(self, **kwargs: Any) -> Any:
        success = await self.ctrl.sleep()
        if not success:
            raise RuntimeError("Failed to put system to sleep.")
        return {"success": True}


class PowerRestartTool(Tool):
    def __init__(self, ctrl: WindowsPowerController):
        self.ctrl = ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="power.restart",
            description="Restart the computer.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.HIGH_RISK

    async def execute(self, **kwargs: Any) -> Any:
        success = await self.ctrl.restart()
        if not success:
            raise RuntimeError("Failed to restart system.")
        return {"success": True}


class PowerShutdownTool(Tool):
    def __init__(self, ctrl: WindowsPowerController):
        self.ctrl = ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="power.shutdown",
            description="Shut down the computer.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.HIGH_RISK

    async def execute(self, **kwargs: Any) -> Any:
        success = await self.ctrl.shutdown()
        if not success:
            raise RuntimeError("Failed to shut down system.")
        return {"success": True}


class ScreenLockTool(Tool):
    def __init__(self, ctrl: WindowsPowerController):
        self.ctrl = ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="screen.lock",
            description="Lock the computer screen / workstation.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.HIGH_RISK

    async def execute(self, **kwargs: Any) -> Any:
        success = await self.ctrl.lock_screen()
        if not success:
            raise RuntimeError("Failed to lock screen.")
        return {"success": True}


class OsPowerTools:
    def __init__(self, ctrl: WindowsPowerController):
        self.ctrl = ctrl

    def register(self, registry):
        registry.register(PowerSleepTool(self.ctrl))
        registry.register(PowerRestartTool(self.ctrl))
        registry.register(PowerShutdownTool(self.ctrl))
        registry.register(ScreenLockTool(self.ctrl))
