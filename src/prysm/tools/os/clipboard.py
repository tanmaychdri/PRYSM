from typing import Any

from prysm.tools.interfaces import BaseTool


class OsClipboardTools(BaseTool):
    """Clipboard read/write tools."""

    def get_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "get_clipboard",
                "description": "Read the current text content of the clipboard.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "set_clipboard",
                "description": "Write text to the clipboard.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to copy to clipboard."}
                    },
                    "required": ["text"],
                },
            },
        ]

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        try:
            import pyperclip
            if tool_name == "get_clipboard":
                return {"clipboard": pyperclip.paste()}
            if tool_name == "set_clipboard":
                pyperclip.copy(arguments["text"])
                return "Copied to clipboard."
        except ImportError:
            return "Error: pyperclip is not installed."
        raise ValueError(f"Unknown tool: {tool_name}")
