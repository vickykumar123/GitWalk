"""
Conversation Controller - Handle conversation retrieval requests.

Endpoints:
- GET /api/conversations/current - Get current conversation for session + repo
"""

from typing import Optional, Dict, List
from fastapi import HTTPException

from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService


class ConversationController:
    """Controller for handling conversation retrieval"""

    @staticmethod
    async def get_current_conversation(
        session_id: str,
        repo_id: str,
        limit: int = 50
    ) -> Dict:
        """
        Get current conversation for a session + repo with its messages.

        Args:
            session_id: Session ID
            repo_id: Repository ID
            limit: Maximum number of messages to return (default 50)

        Returns:
            Dict with conversation metadata and messages

        Raises:
            HTTPException: If conversation not found
        """
        conversation_service = ConversationService()
        message_service = MessageService()

        # Find conversation
        conversation = await conversation_service.find_by_session_and_repo(
            session_id=session_id,
            repo_id=repo_id
        )

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail=f"No conversation found for session {session_id} and repo {repo_id}"
            )

        # Get messages
        messages = await message_service.get_recent_messages(
            conversation_id=conversation.conversation_id,
            limit=limit
        )

        # Convert messages to dict
        message_dicts = [msg.model_dump() for msg in messages]

        # Build response
        return {
            "conversation": conversation.model_dump(),
            "messages": message_dicts,
            "total_messages": len(message_dicts)
        }
