"""
Conversation model for chat history.

A conversation represents an ongoing chat between a user and the AI
for a specific repository within a session.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import uuid4


class Conversation(BaseModel):
    """
    Conversation document in MongoDB.

    Each conversation is scoped to (session_id, repo_id).
    Messages are stored in a separate collection linked by conversation_id.
    """
    conversation_id: str = Field(
        default_factory=lambda: f"conv-{uuid4()}"
    )
    session_id: str = Field(
        ...,
        description="Session ID (links to sessions collection)"
    )
    repo_id: str = Field(
        ...,
        description="Repository ID (links to repositories collection)"
    )
    title: Optional[str] = Field(
        None,
        description="Conversation title (auto-generated from first query)"
    )
    system_prompt: str = Field(
        ...,
        description="System prompt for this conversation (includes repo context)"
    )
    message_count: int = Field(
        default=0,
        description="Total number of messages in this conversation"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Conversation creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last message timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv-123e4567-e89b-12d3-a456-426614174000",
                "session_id": "session-123e4567-e89b-12d3-a456-426614174000",
                "repo_id": "repo-123e4567-e89b-12d3-a456-426614174000",
                "title": "How does the RDB parser work?",
                "system_prompt": "You are a helpful code analysis assistant...",
                "message_count": 6,
                "created_at": "2025-01-22T10:30:00Z",
                "updated_at": "2025-01-22T10:35:00Z"
            }
        }


class ConversationCreate(BaseModel):
    """Request model for creating a new conversation."""
    session_id: str
    repo_id: str
    system_prompt: str
    title: Optional[str] = None


class ConversationUpdate(BaseModel):
    """Request model for updating a conversation."""
    title: Optional[str] = None
    message_count: Optional[int] = None
    updated_at: Optional[datetime] = None
