from typing import Any

from prysm.platform.windows.workspaces import WindowsWorkspaceService
from prysm.tools.interfaces import Tool, ToolRisk, ToolSchema


class WorkspaceListTool(Tool):
    def __init__(self, service: WindowsWorkspaceService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="workspace.list",
            description="List saved workspaces (window arrangements).",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.READ_ONLY

    async def execute(self, **kwargs: Any) -> Any:
        return {"workspaces": self.service.list_workspaces()}


class WorkspaceSaveTool(Tool):
    def __init__(self, service: WindowsWorkspaceService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="workspace.save",
            description="Save the current open windows and their positions as a workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name for the new workspace.",
                    }
                },
                "required": ["name"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.LOW_RISK

    async def execute(self, **kwargs: Any) -> Any:
        name = str(kwargs.get("name"))
        success = self.service.save_workspace(name)
        return {"success": success, "workspace": name}


class WorkspaceLoadTool(Tool):
    def __init__(self, service: WindowsWorkspaceService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="workspace.load",
            description="Load a saved workspace, restoring windows to their saved positions.",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the workspace to load.",
                    }
                },
                "required": ["name"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.LOW_RISK

    async def execute(self, **kwargs: Any) -> Any:
        name = str(kwargs.get("name"))
        success = await self.service.load_workspace(name)
        return {"success": success}


class WorkspaceDeleteTool(Tool):
    def __init__(self, service: WindowsWorkspaceService):
        self.service = service

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="workspace.delete",
            description="Delete a saved workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the workspace to delete.",
                    }
                },
                "required": ["name"],
            },
        )

    @property
    def risk_level(self) -> ToolRisk:
        return ToolRisk.LOW_RISK

    async def execute(self, **kwargs: Any) -> Any:
        name = str(kwargs.get("name"))
        success = self.service.delete_workspace(name)
        return {"success": success}


class OsWorkspaceTools:
    def __init__(self, service: WindowsWorkspaceService):
        self.service = service

    def register(self, registry):
        registry.register(WorkspaceListTool(self.service))
        registry.register(WorkspaceSaveTool(self.service))
        registry.register(WorkspaceLoadTool(self.service))
        registry.register(WorkspaceDeleteTool(self.service))
