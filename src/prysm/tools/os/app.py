import os
import subprocess
import json
from pathlib import Path
from typing import Any

from prysm.tools.interfaces import BaseTool
from prysm.tools.os.app_scanner import scan_and_save_apps


class OsAppTools(BaseTool):
    """Application launch and management tools."""

    def get_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "open_application",
                "description": "Open an application by name (e.g. 'notepad', 'chrome', 'ytmusic', 'spotify') or full path.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "app": {
                            "type": "string",
                            "description": "Application name or full path.",
                        }
                    },
                    "required": ["app"],
                },
            },
            {
                "name": "scan_applications",
                "description": "Scans the PC to discover installed apps and web apps, saving them to the database so they can be opened by name.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
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
        if tool_name == "scan_applications":
            count = scan_and_save_apps()
            return f"Scanned and saved {count} applications."
        if tool_name == "open_url":
            return self._open_url(arguments["url"])
        raise ValueError(f"Unknown tool: {tool_name}")

    def _open_app(self, app: str) -> str:
        app_lower = app.lower().strip()
        apps_file = Path("data/apps.json")
        
        # 1. Try to find it in the scanned database
        if apps_file.exists():
            try:
                with open(apps_file, "r", encoding="utf-8") as f:
                    apps = json.load(f)
                    
                # Exact match
                if app_lower in apps:
                    os.startfile(apps[app_lower])
                    return f"Opened '{app}' from database."
                    
                # Partial match (e.g., "ytmusic" matches "YouTube Music" or vice versa)
                for name, target in apps.items():
                    if app_lower in name or name in app_lower:
                        os.startfile(target)
                        return f"Opened '{name}' ({app})."
            except Exception:
                pass

        # 2. Well-known web apps fallback
        web_apps = {
            "ytmusic": "https://music.youtube.com",
            "youtube music": "https://music.youtube.com",
            "youtube": "https://youtube.com",
            "whatsapp": "https://web.whatsapp.com",
            "twitter": "https://twitter.com",
            "x": "https://x.com",
            "gmail": "https://mail.google.com",
            "netflix": "https://netflix.com",
            "spotify": "https://open.spotify.com",
            "chatgpt": "https://chatgpt.com",
        }
        
        if app_lower in web_apps:
            url = web_apps[app_lower]
            # Try launching as a Chrome PWA, fallback to Edge PWA
            cmd = f'start msedge --app="{url}"'
            try:
                subprocess.Popen(cmd, shell=True)
                return f"Opened '{app}' as a standalone web app."
            except Exception as e:
                return f"Error opening '{app}': {e}"

        # 3. Fallback to basic subprocess if not in database
        try:
            subprocess.Popen(app, shell=True)
            return f"Opened '{app}' (fallback)."
        except Exception as e:
            return f"Error opening '{app}': {e}"

    def _open_url(self, url: str) -> str:
        import webbrowser
        try:
            webbrowser.open(url)
            return f"Opened URL: {url}"
        except Exception as e:
            return f"Error: {e}"
