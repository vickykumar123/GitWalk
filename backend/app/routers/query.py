"""
Query Router - API endpoints for RAG queries.
"""

from fastapi import APIRouter, HTTPException, Header, status
from fastapi.responses import StreamingResponse
from typing import Optional

from app.controllers.query_controller import QueryController, QueryRequest

router = APIRouter(prefix="/api/query", tags=["Query"])


@router.post("/", status_code=status.HTTP_200_OK)
async def process_query(
    request: QueryRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Process user query with RAG (Retrieval Augmented Generation).

    Uses LLM with tool calling to:
    1. Search code semantically
    2. Find files by characteristics
    3. Get repository overview
    4. Fetch specific files
    5. Find specific functions

    **Headers:**
    - `X-API-Key`: Your API key (optional in development, falls back to .env)

    **Request Body:**
    ```json
    {
      "session_id": "866e3a68-0cc8-453f-94c7-d2777ef40ce7",
      "repo_id": "repo-xxx",
      "query": "How does the RDB parser work?",
      "conversation_history": [  // Optional for follow-up questions
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
      ]
    }
    ```

    **Note:** Provider and model are fetched from session preferences. If session has no preferences, falls back to .env settings.

    **Response (Streaming - Server-Sent Events):**

    The endpoint returns a stream of events:

    ```
    data: {"type": "tool_call", "tool": "search_code", "args": {"query": "RDB parser", "top_k": 5}}

    data: {"type": "tool_result", "tool": "search_code", "result_count": 3}

    data: {"type": "answer_chunk", "content": "The"}

    data: {"type": "answer_chunk", "content": " RDB"}

    data: {"type": "answer_chunk", "content": " parser"}

    ...

    data: {"type": "done", "sources": [...], "tool_calls": [...]}
    ```

    **Event Types:**
    - `tool_call`: Tool is being called
    - `tool_result`: Tool execution completed
    - `answer_chunk`: Part of the LLM's answer
    - `done`: Final event with sources and tool_calls
    - `error`: Error occurred

    **Example Queries:**
    - "How does the RDB parser work?" → search_code
    - "Give me files with security issues" → search_files
    - "What does this repo do?" → get_repo_overview
    - "Explain /app/stream.ts" → get_file_by_path
    - "Show me the parseRDBFile function" → find_function
    """
    try:
        return StreamingResponse(
            QueryController.stream_query(request, x_api_key),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable buffering in nginx
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"❌ Query endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )
