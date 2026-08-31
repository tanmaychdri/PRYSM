from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolSchema(BaseModel):
    """Schema defining a tool's capabilities."""
    name: str
    description: str
    parameters: dict[str, Any]

class Tool(ABC):
    """Abstract base class for all tools."""
    
    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        """Return the schema for this tool."""
        pass
        
    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool with the given parameters."""
        pass
