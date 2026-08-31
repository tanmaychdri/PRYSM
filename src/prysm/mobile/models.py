import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"


class ProtocolMessage(BaseModel):
    version: int = 1
    type: MessageType
    device_id: str
    timestamp: float = Field(default_factory=time.time)


class EncryptedPayload(BaseModel):
    nonce: str
    ciphertext: str


class RequestMessage(ProtocolMessage):
    type: MessageType = MessageType.REQUEST
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ResponseMessage(ProtocolMessage):
    type: MessageType = MessageType.RESPONSE
    request_id: str
    success: bool
    payload: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class EventMessage(ProtocolMessage):
    type: MessageType = MessageType.EVENT
    event: str
    payload: dict[str, Any] = Field(default_factory=dict)
