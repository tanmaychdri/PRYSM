from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel


class ToolRisk(str, Enum):
    READ_ONLY = "READ_ONLY"
    LOW_RISK = "LOW_RISK"
    MEDIUM_RISK = "MEDIUM_RISK"
    HIGH_RISK = "HIGH_RISK"


class ToolSchema(BaseModel):
    """Schema defining a tool's capabilities."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema of parameters


class Tool(ABC):
    """Abstract base class for all tools."""

    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        """Return the schema for this tool."""
        pass

    @property
    def risk_level(self) -> ToolRisk:
        """The risk level of this tool."""
        return ToolRisk.LOW_RISK

    @property
    def requires_confirmation(self) -> bool:
        """Whether this tool explicitly requires user confirmation before execution."""
        return self.risk_level in (ToolRisk.MEDIUM_RISK, ToolRisk.HIGH_RISK)

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool with the given parameters."""
        pass
