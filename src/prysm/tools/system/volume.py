from typing import Any

from prysm.platform.windows.audio import AudioController
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class SystemVolumeGetTool(Tool):
    def __init__(self, audio_ctrl: AudioController):
        self.audio_ctrl = audio_ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.volume.get",
            description="Get the current system master volume level (0-100).",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        return {"level": await self.audio_ctrl.get_volume()}


class SystemVolumeSetTool(Tool):
    def __init__(self, audio_ctrl: AudioController):
        self.audio_ctrl = audio_ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.volume.set",
            description="Set the system volume to a specific percentage from 0 to 100. Use this when the user asks to change the computer's overall speaker/headphone volume.",
            parameters={
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "Master volume percentage.",
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

        await self.audio_ctrl.set_volume(level)
        return {"success": True, "level": level}


class SystemVolumeMuteTool(Tool):
    def __init__(self, audio_ctrl: AudioController):
        self.audio_ctrl = audio_ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system.volume.mute",
            description="Mute or unmute the system volume. Use this when the user asks to mute the computer or restore sound.",
            parameters={
                "type": "object",
                "properties": {
                    "mute": {
                        "type": "boolean",
                        "description": "True to mute the audio, false to unmute.",
                    }
                },
                "required": ["mute"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.LOW_RISK

    async def execute(self, **kwargs: Any) -> Any:
        mute = kwargs.get("mute", True)
        if mute:
            await self.audio_ctrl.mute()
        else:
            await self.audio_ctrl.unmute()
        return {"success": True, "muted": mute}
