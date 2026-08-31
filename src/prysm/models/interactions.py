from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class UserInput(BaseModel):
    text: str
    source: str = "text"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolExecutionResult(BaseModel):
    tool_name: str
    result: Any
    success: bool
    error_message: str | None = None


class BrainResponse(BaseModel):
    text: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    finish_reason: str = "stop"
    metadata: dict[str, Any] = Field(default_factory=dict)


class RequestContext(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID | None = None
    input: UserInput
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)
