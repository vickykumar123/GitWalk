from fastapi import HTTPException
from app.services.github_service import GitHubService
from app.services.repository_service import RepositoryService
from app.services.task_service import TaskService
from app.models.schemas import RepositoryCreate, RepositoryResponse, TaskResponse

class RepositoryController:
    """Controller for handling repository-related operations"""

    def __init__(self):
        self.github_service = GitHubService()
        self.repository_service = RepositoryService()
        self.task_service = TaskService()

    async def add_repository(self, request: RepositoryCreate) -> dict:
          """
          Add a new repository and create processing task.

          Args:
              request: RepositoryCreate request model

          Returns:
              Dictionary with repo_id, task_id, and status
          """
          try:
              print(f"🔵 [1/4] Validating GitHub URL: {request.github_url}")
              # 1. Validate GitHub URL
              try:
                  owner, repo_name = self.github_service.parse_github_url(request.github_url)
                  print(f"✅ Parsed: owner={owner}, repo={repo_name}")
              except ValueError as e:
                  print(f"❌ Invalid URL: {e}")
                  raise HTTPException(status_code=400, detail=str(e))

              print(f"🔵 [2/4] Creating repository document...")
              # 2. Create repository document
              repo_id = await self.repository_service.create_repository(
                  github_url=request.github_url,
                  session_id=request.session_id
              )
              print(f"✅ Repository created: {repo_id}")

              print(f"🔵 [3/4] Creating background task...")
              # 3. Create task for background processing
              task_id = await self.task_service.create_task(
                  task_type="process_repository",
                  payload={
                      "repo_id": repo_id,
                      "session_id": request.session_id,
                      "owner": owner,
                      "repo_name": repo_name
                  }
              )
              print(f"✅ Task created: {task_id}")

              print(f"🔵 [4/4] Linking task to repository...")
              # 4. Link task to repository
              await self.repository_service.update_task_id(repo_id, task_id)
              print(f"✅ Task linked successfully")

              print(f"🎉 Repository added successfully!")
              return {
                  "repo_id": repo_id,
                  "task_id": task_id,
                  "status": "queued",
                  "message": "Repository added successfully. Processing will begin shortly."
              }

          except HTTPException:
              raise
          except Exception as e:
              print(f"❌ Error in add_repository: {str(e)}")
              raise HTTPException(status_code=500, detail=f"Failed to add repository: {str(e)}")
        
    async def get_repository(self, repo_id: str) -> RepositoryResponse:
          """
          Retrieve repository details by repo_id.

          Args:
              repo_id: Repository ID

          Returns:
              RepositoryResponse model
          """
          repo_doc = await self.repository_service.get_repository(repo_id)
          if not repo_doc:
              raise HTTPException(status_code=404, detail="Repository not found")

          return self._convert_to_response(repo_doc)
    
    async def get_file_tree(self, repo_id: str) -> dict:
          """
          Retrieve the file tree of a repository.

          Args:
              repo_id: Repository ID

          Returns:
              Dictionary representing the file tree
          """
          repo_doc = await self.repository_service.get_repository(repo_id)
          if not repo_doc:
              raise HTTPException(status_code=404, detail="Repository not found")

          file_tree =  repo_doc.get("file_tree", {})
          if not file_tree:
              return {
                  "message": "File tree not yet available. Repository may still be processing.",
                  "status": repo_doc.get("status", "unknown")
              }
          return file_tree
    
    async def get_task_status(self, task_id: str) -> TaskResponse:
        """
        Get the status of a processing task.
        """

        task_doc = await self.task_service.get_task(task_id)
        if not task_doc:
            raise HTTPException(status_code=404, detail="Task not found")

        return TaskResponse(
            task_id=task_doc["task_id"],
            status=task_doc["status"],
            progress=task_doc["progress"],
            error_message=task_doc.get("error_message"),
            created_at=task_doc["created_at"],
            started_at=task_doc.get("started_at"),
            completed_at=task_doc.get("completed_at")
        )
        
    def _convert_to_response(self, repo_doc: dict) -> RepositoryResponse:
        """Convert repository document to RepositoryResponse model"""
        return RepositoryResponse(
            repo_id=repo_doc["repo_id"],
            session_id=repo_doc["session_id"],
            github_url=repo_doc["github_url"],
            owner=repo_doc.get("owner", ""),
            repo_name=repo_doc.get("repo_name", ""),
            full_name=repo_doc.get("full_name", ""),
            description=repo_doc.get("description"),
            default_branch=repo_doc.get("default_branch", "main"),
            language=repo_doc.get("language"),
            stars=repo_doc.get("stars", 0),
            forks=repo_doc.get("forks", 0),
            status=repo_doc["status"],
            task_id=repo_doc.get("task_id"),
            error_message=repo_doc.get("error_message"),
            file_count=repo_doc.get("file_count", 0),
            total_size_bytes=repo_doc.get("total_size_bytes", 0),
            languages_breakdown=repo_doc.get("languages_breakdown"),
            created_at=repo_doc["created_at"],
            updated_at=repo_doc["updated_at"],
            last_fetched=repo_doc.get("last_fetched")
        )
