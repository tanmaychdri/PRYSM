from typing import Any

from prysm.tools.interfaces import BaseTool


class OsVolumeTools(BaseTool):
    """System volume control tools (Windows)."""

    def get_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "set_volume",
                "description": "Set the system master volume level (0-100).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "level": {
                            "type": "integer",
                            "description": "Volume level from 0 (mute) to 100 (max).",
                        }
                    },
                    "required": ["level"],
                },
            },
            {
                "name": "get_volume",
                "description": "Get the current system master volume level.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "mute_volume",
                "description": "Mute or unmute the system audio.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mute": {"type": "boolean", "description": "True to mute, False to unmute."}
                    },
                    "required": ["mute"],
                },
            },
        ]

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL
            import ctypes

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))

            if tool_name == "get_volume":
                level = round(volume.GetMasterVolumeLevelScalar() * 100)
                return {"volume": level}

            if tool_name == "set_volume":
                level = max(0, min(100, int(arguments["level"])))
                volume.SetMasterVolumeLevelScalar(level / 100.0, None)
                return f"Volume set to {level}%."

            if tool_name == "mute_volume":
                mute = bool(arguments["mute"])
                volume.SetMute(mute, None)
                return "Muted." if mute else "Unmuted."

        except ImportError:
            return "Error: pycaw is not installed. Run: pip install pycaw"
        except Exception as e:
            return f"Error: {e}"

        raise ValueError(f"Unknown tool: {tool_name}")
