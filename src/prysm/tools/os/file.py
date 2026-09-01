from typing import Any

from prysm.platform.windows.files import WindowsFileController
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class FileSearchTool(Tool):
    def __init__(self, ctrl: WindowsFileController):
        self.ctrl = ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="file.search",
            description="Search for files by name in a specified directory.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search term to match against file names.",
                    },
                    "directory": {
                        "type": "string",
                        "description": "The absolute path to the directory to search in (e.g., 'C:\\Users\\name\\Documents'). Must be an allowed root.",
                    },
                    "extension": {
                        "type": "string",
                        "description": "Optional file extension to filter by (e.g., '.pdf').",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default 20).",
                    },
                },
                "required": ["query", "directory"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        query = kwargs.get("query")
        directory = kwargs.get("directory")
        extension = kwargs.get("extension")
        max_results = kwargs.get("max_results", 20)

        if not query or not directory:
            raise ValueError("query and directory are required.")

        results = await self.ctrl.search_files(
            query=query,
            directory=directory,
            extension=extension,
            max_results=max_results,
        )
        return {"results": results, "count": len(results)}


class RecycleBinEmptyTool(Tool):
    def __init__(self, ctrl: WindowsFileController):
        self.ctrl = ctrl

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="recycle_bin.empty",
            description="Empty the Windows Recycle Bin.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.HIGH_RISK

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> Any:
        success = await self.ctrl.empty_recycle_bin()
        if not success:
            raise RuntimeError("Failed to empty recycle bin.")
        return {"success": True}


class OsFileTools:
    def __init__(self, ctrl: WindowsFileController):
        self.ctrl = ctrl

    def register(self, registry):
        registry.register(FileSearchTool(self.ctrl))
        registry.register(RecycleBinEmptyTool(self.ctrl))
