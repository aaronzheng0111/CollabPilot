from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


Role = Literal["system", "user", "assistant", "tool"]
RiskLevel = Literal["read", "write", "external", "dangerous"]


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    role: Role
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    content: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    provider: str
    model: str
    usage: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    ok: bool
    data: Any = None
    display: str = ""
    error_code: str | None = None
    retryable: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatResult(BaseModel):
    session_id: UUID
    turn_id: UUID
    content: str
    provider: str
    model: str
    tool_calls: int = 0
    goal_status: str | None = None
    pending_decision: str | None = None


class StoredMessage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    turn_id: UUID
    message: Message
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProjectSummary(BaseModel):
    """One product / campaign chat. Backed by a session row."""

    session_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
