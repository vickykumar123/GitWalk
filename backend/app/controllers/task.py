"""
Task Controller - Business logic for task operations
"""
from typing import Optional, Dict
from app.services.task_service import TaskService


class TaskController:
    """Controller for task-related operations"""

    def __init__(self):
        self.task_service = TaskService()

    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        Get task status and progress.

        Args:
            task_id: Task ID

        Returns:
            Task document with status, progress, and metadata
        """
        task = await self.task_service.get_task(task_id)

        if not task:
            return None

        # Format response
        return {
            "task_id": task["task_id"],
            "task_type": task["task_type"],
            "status": task["status"],
            "progress": task.get("progress", {}),
            "error_message": task.get("error_message"),
            "result": task.get("result"),
            "created_at": task["created_at"],
            "started_at": task.get("started_at"),
            "completed_at": task.get("completed_at"),
            "updated_at": task["updated_at"]
        }
