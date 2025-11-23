"""
Message Service - CRUD operations for chat messages.

Handles:
- Creating new messages (user and assistant)
- Fetching recent messages for context
- Building OpenAI-format message arrays
"""

from typing import List, Dict, Optional
from datetime import datetime

from app.database import db
from app.models.message import Message, MessageCreate


class MessageService:
    """Service for managing chat messages."""

    def __init__(self):
        """Initialize message service."""
        self.database = db.get_database()
        self.collection = self.database["messages"]

    async def create(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sequence_number: int,
        tool_calls: Optional[List[Dict]] = None
    ) -> Message:
        """
        Create a new message.

        Args:
            conversation_id: Conversation ID
            role: Message role (user or assistant)
            content: Message content
            sequence_number: Message order in conversation
            tool_calls: Optional tool calls (for assistant messages)

        Returns:
            Created message
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            sequence_number=sequence_number
        )

        # Convert to dict and insert
        doc = message.model_dump()
        await self.collection.insert_one(doc)

        return message

    async def get_recent_messages(
        self,
        conversation_id: str,
        limit: int = 20
    ) -> List[Message]:
        """
        Get recent messages for a conversation.

        Fetches the last N messages, sorted by sequence_number.

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to fetch (default 20)

        Returns:
            List of recent messages in chronological order
        """
        # Fetch last N messages, sorted descending
        cursor = self.collection.find(
            {"conversation_id": conversation_id}
        ).sort("sequence_number", -1).limit(limit)

        messages = await cursor.to_list(length=limit)

        # Reverse to get chronological order (oldest first)
        messages.reverse()

        # Convert to Message objects
        result = []
        for doc in messages:
            doc.pop("_id", None)
            result.append(Message(**doc))

        return result

    async def get_recent_messages_openai_format(
        self,
        conversation_id: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get recent messages in OpenAI format.

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to fetch (default 20)

        Returns:
            List of messages in OpenAI format
        """
        messages = await self.get_recent_messages(conversation_id, limit)
        return [msg.to_openai_format() for msg in messages]

    async def count_messages(self, conversation_id: str) -> int:
        """
        Count total messages in a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Total number of messages
        """
        return await self.collection.count_documents({
            "conversation_id": conversation_id
        })

    async def get_next_sequence_number(self, conversation_id: str) -> int:
        """
        Get the next sequence number for a new message.

        Args:
            conversation_id: Conversation ID

        Returns:
            Next sequence number (1 if no messages exist)
        """
        # Find the highest sequence number
        result = await self.collection.find_one(
            {"conversation_id": conversation_id},
            sort=[("sequence_number", -1)]
        )

        if result:
            return result["sequence_number"] + 1
        else:
            return 1

    async def bulk_create(
        self,
        conversation_id: str,
        messages: List[Dict]
    ) -> List[Message]:
        """
        Create multiple messages at once.

        Useful for saving multiple messages (user query + assistant response + tool results).

        Args:
            conversation_id: Conversation ID
            messages: List of message dicts with role, content, etc.

        Returns:
            List of created messages
        """
        # Get starting sequence number
        next_seq = await self.get_next_sequence_number(conversation_id)

        created_messages = []
        docs_to_insert = []

        for i, msg_data in enumerate(messages):
            message = Message(
                conversation_id=conversation_id,
                role=msg_data["role"],
                content=msg_data["content"],
                tool_calls=msg_data.get("tool_calls"),
                sequence_number=next_seq + i
            )
            created_messages.append(message)
            docs_to_insert.append(message.model_dump())

        # Bulk insert
        if docs_to_insert:
            await self.collection.insert_many(docs_to_insert)

        return created_messages
