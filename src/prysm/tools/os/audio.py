from typing import Any

from prysm.platform.windows.audio import WindowsAudioController
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class AudioVolumeGetTool(Tool):
    def __init__(self, ctrl: WindowsAudioController):
        self.ctrl = ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="audio.volume.get",
            description="Get the current system master volume level (0-100).",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        return {"level": await self.ctrl.get_volume()}


class AudioVolumeSetTool(Tool):
    def __init__(self, ctrl: WindowsAudioController):
        self.ctrl = ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="audio.volume.set",
            description="Set the system volume to a specific percentage from 0 to 100.",
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

        await self.ctrl.set_volume(level)
        return {"success": True, "level": level}


class AudioMuteTool(Tool):
    def __init__(self, ctrl: WindowsAudioController):
        self.ctrl = ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="audio.mute",
            description="Mute or unmute the system volume.",
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
            await self.ctrl.mute()
        else:
            await self.ctrl.unmute()
        return {"success": True, "muted": mute}


class OsAudioTools:
    def __init__(self, ctrl: WindowsAudioController):
        self.ctrl = ctrl

    def register(self, registry):
        registry.register(AudioVolumeGetTool(self.ctrl))
        registry.register(AudioVolumeSetTool(self.ctrl))
        registry.register(AudioMuteTool(self.ctrl))
