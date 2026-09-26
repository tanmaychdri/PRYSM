import datetime
import platform
import subprocess
from typing import Any

import psutil

from prysm.tools.interfaces import BaseTool


class OsSystemTools(BaseTool):
    """System information and control tools."""

    def get_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "get_system_info",
                "description": "Get current system information: time, date, CPU, RAM, OS.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "run_shell_command",
                "description": "Run a PowerShell command and return its output. Use with caution.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The PowerShell command to run."}
                    },
                    "required": ["command"],
                },
            },
        ]

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        if tool_name == "get_system_info":
            return self._get_system_info()
        if tool_name == "run_shell_command":
            return self._run_shell(arguments["command"])
        raise ValueError(f"Unknown tool: {tool_name}")

    def _get_system_info(self) -> dict:
        now = datetime.datetime.now()
        return {
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "day": now.strftime("%A"),
            "os": platform.system(),
            "os_version": platform.version(),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 1),
            "ram_used_percent": psutil.virtual_memory().percent,
        }

    def _run_shell(self, command: str) -> str:
        try:
            result = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True,
                text=True,
                timeout=15,
            )
            output = result.stdout.strip() or result.stderr.strip()
            return output or "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: command timed out"
        except Exception as e:
            return f"Error: {e}"
