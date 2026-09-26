import subprocess
from typing import Any

from prysm.tools.interfaces import BaseTool


class OsAppTools(BaseTool):
    """Application launch and management tools."""

    def get_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "open_application",
                "description": "Open an application by name or executable path.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "app": {
                            "type": "string",
                            "description": "Application name (e.g. 'notepad', 'chrome', 'spotify') or full path.",
                        }
                    },
                    "required": ["app"],
                },
            },
            {
                "name": "open_url",
                "description": "Open a URL in the default web browser.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The URL to open."}
                    },
                    "required": ["url"],
                },
            },
        ]

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        if tool_name == "open_application":
            return self._open_app(arguments["app"])
        if tool_name == "open_url":
            return self._open_url(arguments["url"])
        raise ValueError(f"Unknown tool: {tool_name}")

    def _open_app(self, app: str) -> str:
        try:
            subprocess.Popen(app, shell=True)
            return f"Opened '{app}'."
        except Exception as e:
            return f"Error opening '{app}': {e}"

    def _open_url(self, url: str) -> str:
        import webbrowser
        try:
            webbrowser.open(url)
            return f"Opened URL: {url}"
        except Exception as e:
            return f"Error: {e}"
