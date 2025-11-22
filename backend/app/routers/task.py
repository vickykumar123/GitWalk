"""
Task Router - API endpoints for task status and progress tracking
"""
from fastapi import APIRouter, HTTPException
from app.controllers.task import TaskController

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])
controller = TaskController()


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """
    Get task status and progress.

    Returns task details including:
    - status (pending/in_progress/completed/failed)
    - progress (current_step, processed_files, total_files)
    - error_message (if failed)
    - timestamps
    """
    result = await controller.get_task_status(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result
