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
    call_id: str
    tool_name: str
    result: Any
    success: bool
    error_message: str | None = None
    duration_s: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMToolCall(BaseModel):
    call_id: str
    tool_name: str
    arguments: dict[str, Any]


class LLMMessage(BaseModel):
    role: str  # system, user, assistant, tool
    content: str | None = None
    tool_calls: list[LLMToolCall] | None = None
    tool_call_id: str | None = None


class Conversation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    messages: list[LLMMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def add_message(self, message: LLMMessage) -> None:
        self.messages.append(message)
        self.updated_at = datetime.now(UTC)


class BrainResponse(BaseModel):
    text: str | None = None
    tool_calls: list[LLMToolCall] = Field(default_factory=list)
    finish_reason: str = "stop"
    metadata: dict[str, Any] = Field(default_factory=dict)


class RequestContext(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID | None = None
    input: UserInput
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)
