from fastapi import APIRouter, BackgroundTasks
from app.controllers.repository import RepositoryController
from app.models.schemas import RepositoryCreate, RepositoryResponse, TaskResponse

router = APIRouter(prefix="/api/repositories", tags=["Repositories"])
controller = RepositoryController()

@router.post("/", response_model=dict)
async def add_repository(request: RepositoryCreate, background_tasks: BackgroundTasks):
    """Add a new repository and start background file processing."""
    return await controller.add_repository(request, background_tasks)

@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(repo_id: str):
    return await controller.get_repository(repo_id)

@router.get("/{repo_id}/tree", response_model=dict)
async def get_repository_tree(repo_id: str):
    return await controller.get_file_tree(repo_id)

@router.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def get_task_status(task_id: str):
    return await controller.get_task_status(task_id)