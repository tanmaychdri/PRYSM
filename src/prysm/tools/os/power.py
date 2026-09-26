import subprocess
from typing import Any

from prysm.tools.interfaces import BaseTool


class OsPowerTools(BaseTool):
    """Power management tools: shutdown, restart, sleep, lock."""

    def get_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "power_action",
                "description": "Perform a power action on the PC: shutdown, restart, sleep, or lock.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["shutdown", "restart", "sleep", "lock"],
                            "description": "The power action to perform.",
                        },
                        "delay_seconds": {
                            "type": "integer",
                            "description": "Delay in seconds before the action (default 0).",
                            "default": 0,
                        },
                    },
                    "required": ["action"],
                },
            }
        ]

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        action = arguments["action"]
        delay = int(arguments.get("delay_seconds", 0))

        commands = {
            "shutdown": ["shutdown", "/s", "/t", str(delay)],
            "restart": ["shutdown", "/r", "/t", str(delay)],
            "sleep": ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
            "lock": ["rundll32.exe", "user32.dll,LockWorkStation"],
        }

        if action not in commands:
            return f"Unknown action: {action}"

        try:
            subprocess.Popen(commands[action])
            return f"Power action '{action}' initiated."
        except Exception as e:
            return f"Error: {e}"
