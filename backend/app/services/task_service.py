from typing import Optional, Dict
from datetime import datetime
import uuid
from app.database import db

class TaskService:
    """Service for managing tasks queue and progress tracking"""

    def __init__(self):
        self.collection_name = "tasks"
    
    async def create_task(self, task_type:str, payload:dict) -> str:
        """Create a new task in the queue"""
        database = db.get_database()
        collection = database[self.collection_name]
        task_id = str(uuid.uuid4())
        now = datetime.now()
        task_doc = {
            "task_id": task_id,
            "task_type": task_type,
            "status": "pending",
            "payload": payload,
            "progress": {
                "total_files": 0,
                "processed_files": 0,
                "current_step": "queued"
            },
            "attempts": 0,
            "max_attempts": 3,
            "error_message": None,
            "created_at": now,
            "started_at": None,
            "completed_at": None,
            "updated_at": now
        }

        await collection.insert_one(task_doc)
        return task_id
    
    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Retrieve task details by task_id"""
        database = db.get_database()
        collection = database[self.collection_name]
        task_doc = await collection.find_one({"task_id": task_id})
        return task_doc
    
    async def update_progress(self, task_id:str, processed_files:int, total_files:int) -> bool:
        """Update task progress with processed/total file counts"""
        database = db.get_database()
        collection = database[self.collection_name]

        # Auto-generate current_step description
        if processed_files == 0:
            current_step = "Starting file processing"
        elif processed_files >= total_files:
            current_step = "Finalizing"
        else:
            percentage = int((processed_files / total_files) * 100)
            current_step = f"Processing files ({percentage}% complete)"

        result = await collection.update_one(
            {"task_id": task_id},
            {"$set": {
                "status":"in_progress",
                "progress.current_step": current_step,
                "progress.total_files": total_files,
                "progress.processed_files": processed_files,
                "updated_at": datetime.now()
            }}
        )
        return result.modified_count > 0

    async def complete_task(self, task_id: str, result: Optional[Dict] = None) -> bool:
        database = db.get_database()
        collection = database[self.collection_name]

        update_fields = {
            "status": "completed",
            "completed_at": datetime.now(),
            "updated_at": datetime.now()
        }

        if result:
            update_fields["result"] = result

        update_result = await collection.update_one(
            {"task_id": task_id},
            {"$set": update_fields}
        )
        return update_result.modified_count > 0
    
    async def fail_task(self, task_id:str, error_message:str) -> bool:
        database = db.get_database()
        collection = database[self.collection_name]
        result = await collection.update_one(
            {"task_id": task_id},
            {"$set": {
                "status":"failed",
                "error_message": error_message,
                "updated_at": datetime.now()
            }}
        )
        return result.modified_count > 0