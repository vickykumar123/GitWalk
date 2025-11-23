"""
Conversation Service - CRUD operations for chat conversations.

Handles:
- Creating new conversations
- Finding conversations by session_id + repo_id
- Updating conversation metadata (title, message_count)
"""

from typing import Optional
from datetime import datetime

from app.database import db
from app.models.conversation import Conversation, ConversationCreate, ConversationUpdate


class ConversationService:
    """Service for managing conversations."""

    def __init__(self):
        """Initialize conversation service."""
        self.database = db.get_database()
        self.collection = self.database["conversations"]

    async def find_by_session_and_repo(
        self,
        session_id: str,
        repo_id: str
    ) -> Optional[Conversation]:
        """
        Find existing conversation for a session + repo.

        Args:
            session_id: Session ID
            repo_id: Repository ID

        Returns:
            Conversation if found, None otherwise
        """
        doc = await self.collection.find_one({
            "session_id": session_id,
            "repo_id": repo_id
        })

        if doc:
            # Remove MongoDB's _id field
            doc.pop("_id", None)
            return Conversation(**doc)

        return None

    async def create(
        self,
        session_id: str,
        repo_id: str,
        system_prompt: str,
        title: Optional[str] = None
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            session_id: Session ID
            repo_id: Repository ID
            system_prompt: System prompt for this conversation
            title: Optional conversation title

        Returns:
            Created conversation
        """
        conversation = Conversation(
            session_id=session_id,
            repo_id=repo_id,
            system_prompt=system_prompt,
            title=title,
            message_count=0
        )

        # Convert to dict and insert
        doc = conversation.model_dump()
        await self.collection.insert_one(doc)

        print(f"✅ Created conversation: {conversation.conversation_id}")
        return conversation

    async def update(
        self,
        conversation_id: str,
        update_data: ConversationUpdate
    ) -> bool:
        """
        Update conversation metadata.

        Args:
            conversation_id: Conversation ID to update
            update_data: Fields to update

        Returns:
            True if updated successfully
        """
        # Build update dict (only non-None fields)
        update_dict = {}
        if update_data.title is not None:
            update_dict["title"] = update_data.title
        if update_data.message_count is not None:
            update_dict["message_count"] = update_data.message_count
        if update_data.updated_at is not None:
            update_dict["updated_at"] = update_data.updated_at
        else:
            # Always update timestamp
            update_dict["updated_at"] = datetime.utcnow()

        if not update_dict:
            return False

        result = await self.collection.update_one(
            {"conversation_id": conversation_id},
            {"$set": update_dict}
        )

        return result.modified_count > 0

    async def increment_message_count(
        self,
        conversation_id: str,
        increment: int = 1
    ) -> bool:
        """
        Increment message count for a conversation.

        Args:
            conversation_id: Conversation ID
            increment: Number to increment by (default 1)

        Returns:
            True if updated successfully
        """
        result = await self.collection.update_one(
            {"conversation_id": conversation_id},
            {
                "$inc": {"message_count": increment},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        return result.modified_count > 0

    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation if found, None otherwise
        """
        doc = await self.collection.find_one({"conversation_id": conversation_id})

        if doc:
            doc.pop("_id", None)
            return Conversation(**doc)

        return None

    async def find_or_create(
        self,
        session_id: str,
        repo_id: str,
        system_prompt: str,
        title: Optional[str] = None
    ) -> Conversation:
        """
        Find existing conversation or create new one.

        Args:
            session_id: Session ID
            repo_id: Repository ID
            system_prompt: System prompt (used if creating new)
            title: Optional title (used if creating new)

        Returns:
            Existing or newly created conversation
        """
        # Try to find existing
        existing = await self.find_by_session_and_repo(session_id, repo_id)
        if existing:
            return existing

        # Create new
        return await self.create(
            session_id=session_id,
            repo_id=repo_id,
            system_prompt=system_prompt,
            title=title
        )
