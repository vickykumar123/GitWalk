"""
Conversation Router - API endpoints for conversation retrieval.
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.controllers.conversation_controller import ConversationController

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


@router.get("/current", status_code=status.HTTP_200_OK)
async def get_current_conversation(
    session_id: str = Query(..., description="Session ID"),
    repo_id: str = Query(..., description="Repository ID"),
    limit: int = Query(50, description="Maximum number of messages to return", ge=1, le=100)
):
    """
    Get current conversation for a session + repository.

    Returns conversation metadata and messages.

    **Query Parameters:**
    - `session_id`: Session ID
    - `repo_id`: Repository ID
    - `limit`: Maximum number of messages to return (default 50, max 100)

    **Response:**
    ```json
    {
      "conversation": {
        "conversation_id": "conv-xxx",
        "session_id": "session-xxx",
        "repo_id": "repo-xxx",
        "title": "How does the RDB parser work?",
        "system_prompt": "You are a helpful...",
        "message_count": 6,
        "created_at": "2025-01-22T10:30:00Z",
        "updated_at": "2025-01-22T10:35:00Z"
      },
      "messages": [
        {
          "message_id": "msg-xxx",
          "conversation_id": "conv-xxx",
          "role": "user",
          "content": "How does the RDB parser work?",
          "sequence_number": 1,
          "timestamp": "2025-01-22T10:30:00Z"
        },
        {
          "message_id": "msg-yyy",
          "conversation_id": "conv-xxx",
          "role": "assistant",
          "content": "The RDB parser...",
          "tool_calls": [...],
          "sequence_number": 2,
          "timestamp": "2025-01-22T10:30:15Z"
        }
      ],
      "total_messages": 2
    }
    ```

    **Example:**
    ```
    GET /api/conversations/current?session_id=session-123&repo_id=repo-456
    ```
    """
    try:
        return await ConversationController.get_current_conversation(
            session_id=session_id,
            repo_id=repo_id,
            limit=limit
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversation: {str(e)}"
        )
