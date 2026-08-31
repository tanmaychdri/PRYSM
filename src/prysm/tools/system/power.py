from typing import Any

from prysm.platform.windows.power import PowerController
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class SystemPowerSleepTool(Tool):
    def __init__(self, power_ctrl: PowerController):
        self.power_ctrl = power_ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.power.sleep",
            description="Put the system to sleep (suspend).",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.HIGH_RISK

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> Any:
        success = await self.power_ctrl.sleep()
        if not success:
            raise RuntimeError("Failed to put system to sleep.")
        return {"success": True}


class SystemPowerRestartTool(Tool):
    def __init__(self, power_ctrl: PowerController):
        self.power_ctrl = power_ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.power.restart",
            description="Restart the computer.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.HIGH_RISK

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> Any:
        success = await self.power_ctrl.restart()
        if not success:
            raise RuntimeError("Failed to restart system.")
        return {"success": True}


class SystemPowerShutdownTool(Tool):
    def __init__(self, power_ctrl: PowerController):
        self.power_ctrl = power_ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.power.shutdown",
            description="Shut down the computer.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.HIGH_RISK

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> Any:
        success = await self.power_ctrl.shutdown()
        if not success:
            raise RuntimeError("Failed to shut down system.")
        return {"success": True}


class SystemScreenLockTool(Tool):
    def __init__(self, power_ctrl: PowerController):
        self.power_ctrl = power_ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.screen.lock",
            description="Lock the computer screen / workstation.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.HIGH_RISK

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> Any:
        success = await self.power_ctrl.lock_screen()
        if not success:
            raise RuntimeError("Failed to lock screen.")
        return {"success": True}
