"""Chat request and response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """Request body for POST /chat."""

    message: str = Field(min_length=1)
    conversation_id: uuid.UUID | None = None


class MessageResponse(BaseModel):
    """Serialized conversation message."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    created_at: datetime
    provider_metadata: dict | None = None


class ConversationResponse(BaseModel):
    """Serialized conversation with its messages."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = Field(default_factory=list)


class HistoryResponse(BaseModel):
    """Response body for GET /chat/history."""

    conversations: list[ConversationResponse] = Field(default_factory=list)
