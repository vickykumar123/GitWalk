"""
Message model for chat history.

Messages are stored separately from conversations to avoid document size limits.
Each message is linked to a conversation via conversation_id.

Only user and assistant messages are stored (no system or tool messages).
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Literal
from uuid import uuid4


class Message(BaseModel):
    """
    Message document in MongoDB.

    Stores individual messages in OpenAI format, linked to a conversation.
    Only stores user and assistant messages.
    """
    message_id: str = Field(
        default_factory=lambda: f"msg-{uuid4()}"
    )
    conversation_id: str = Field(
        ...,
        description="Conversation ID (links to conversations collection)"
    )
    role: Literal["user", "assistant"] = Field(
        ...,
        description="Message role (user or assistant)"
    )
    content: str = Field(
        ...,
        description="Message content"
    )
    tool_calls: Optional[List[Dict]] = Field(
        None,
        description="Tool calls made by assistant (for assistant messages only)"
    )
    sequence_number: int = Field(
        ...,
        description="Order within conversation (1, 2, 3...)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg-123e4567-e89b-12d3-a456-426614174000",
                "conversation_id": "conv-123e4567-e89b-12d3-a456-426614174000",
                "role": "user",
                "content": "How does the RDB parser work?",
                "sequence_number": 1,
                "timestamp": "2025-01-22T10:30:00Z"
            }
        }

    def to_openai_format(self) -> Dict:
        """
        Convert message to OpenAI chat format.

        Returns:
            Dict in OpenAI message format
        """
        msg = {
            "role": self.role,
            "content": self.content
        }

        # Add tool_calls if present (assistant messages)
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls

        return msg


class MessageCreate(BaseModel):
    """Request model for creating a new message."""
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    tool_calls: Optional[List[Dict]] = None
    sequence_number: int
