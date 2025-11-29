# Pydantic models for request/response validation
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class SessionPreferences(BaseModel):
    """User preferences for AI and UI"""

    # AI Chat Settings (REQUIRED when preferences are set)
    ai_provider: str = Field(..., description="AI provider: openai, together, groq, grok, openrouter")
    ai_model: str = Field(..., description="AI model name: gpt-4o-mini, llama-3.1-70b, etc.")

    # Embedding Settings (uses same provider as AI chat)
    embedding_provider: Optional[str] = Field(
        None,
        description="Embedding provider: uses same provider as ai_provider"
    )
    embedding_model: Optional[str] = Field(
        None,
        description="Embedding model: text-embedding-3-small (only if provider is openai)"
    )

    # UI Settings (OPTIONAL)
    theme: Optional[str] = Field("dark", description="UI theme: light or dark")

    class Config:
        json_schema_extra = {
            "example": {
                "ai_provider": "openai",
                "ai_model": "gpt-4o-mini",
                "embedding_provider": "openai",
                "embedding_model": "text-embedding-3-small",
                "theme": "dark"
            }
        }


class SessionResponse(BaseModel):
    """Response model for session data"""

    session_id: str
    created_at: datetime
    updated_at: datetime
    last_accessed: datetime
    repositories: List[str] = Field(default_factory=list)  # List of ObjectId strings
    preferences: Optional[SessionPreferences] = None  # Can be null initially

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
                "last_accessed": "2025-01-15T10:00:00Z",
                "repositories": [
                    "507f1f77bcf86cd799439012",
                    "507f1f77bcf86cd799439013"
                ],
                "preferences": {
                    "ai_provider": "openai",
                    "ai_model": "gpt-4o-mini",
                    "embedding_provider": "openai",
                    "embedding_model": "text-embedding-3-small",
                    "theme": "dark"
                }
            }
        }


class SessionUpdatePreferences(BaseModel):
    """Request model for updating session preferences"""

    ai_provider: str = Field(..., description="AI provider (required)")
    ai_model: str = Field(..., description="AI model (required)")
    embedding_provider: Optional[str] = Field(None, description="Embedding provider (optional)")
    embedding_model: Optional[str] = Field(None, description="Embedding model (optional)")
    theme: Optional[str] = Field("dark", description="UI theme")

    class Config:
        json_schema_extra = {
            "example": {
                "ai_provider": "openai",
                "ai_model": "gpt-4o-mini",
                "embedding_provider": None,  # Uses same as ai_provider
                "theme": "dark"
            }
        }
# ==================== Task Models ====================

class TaskProgress(BaseModel):
      """Progress information for a task."""
      total_files: int = Field(0, description="Total number of files to process")
      processed_files: int = Field(0, description="Number of files processed so far")
      current_step: str = Field("queued", description="Current processing step: queued, fetching, parsing, embedding")

      class Config:
          json_schema_extra = {
              "example": {
                  "total_files": 350,
                  "processed_files": 200,
                  "current_step": "parsing"
              }
          }


class TaskResponse(BaseModel):
      """Response model for task status."""
      task_id: str
      status: str = Field(..., description="Task status: pending, in_progress, completed, failed")
      progress: TaskProgress
      error_message: Optional[str] = None
      created_at: datetime
      started_at: Optional[datetime] = None
      completed_at: Optional[datetime] = None

      class Config:
          json_schema_extra = {
              "example": {
                  "task_id": "task-xyz789",
                  "status": "in_progress",
                  "progress": {
                      "total_files": 350,
                      "processed_files": 200,
                      "current_step": "parsing"
                  },
                  "error_message": None,
                  "created_at": "2025-01-16T10:00:00Z",
                  "started_at": "2025-01-16T10:00:05Z",
                  "completed_at": None
              }
          }


  # ==================== Repository Models ====================

class RepositoryCreate(BaseModel):
      """Request model for creating/adding a repository."""
      github_url: str = Field(..., description="GitHub repository URL (e.g., https://github.com/owner/repo)")
      session_id: str = Field(..., description="Session ID from localStorage")

      class Config:
          json_schema_extra = {
              "example": {
                  "github_url": "https://github.com/microsoft/vscode",
                  "session_id": "550e8400-e29b-41d4-a716-446655440000"
              }
          }


class RepositoryResponse(BaseModel):
      """Response model for repository data."""
      repo_id: str
      session_id: str
      github_url: str
      owner: str
      repo_name: str
      full_name: str

      # Optional metadata
      description: Optional[str] = None
      default_branch: Optional[str] = "main"
      language: Optional[str] = None
      stars: Optional[int] = 0
      forks: Optional[int] = 0

      # Processing status
      status: str = Field(..., description="Repository processing status")
      task_id: Optional[str] = None
      error_message: Optional[str] = None

      # Statistics
      file_count: int = 0
      total_size_bytes: int = 0
      languages_breakdown: Optional[dict] = None

      # File tree structure
      file_tree: Optional[dict] = Field(default=None, description="Nested file tree structure")

      # AI-generated content
      overview: Optional[str] = None
      overview_generated_at: Optional[datetime] = None

      # Timestamps
      created_at: datetime
      updated_at: datetime
      last_fetched: Optional[datetime] = None

      class Config:
          json_schema_extra = {
              "example": {
                  "repo_id": "repo-abc123",
                  "session_id": "550e8400-e29b-41d4-a716-446655440000",
                  "github_url": "https://github.com/microsoft/vscode",
                  "owner": "microsoft",
                  "repo_name": "vscode",
                  "full_name": "microsoft/vscode",
                  "description": "Visual Studio Code",
                  "default_branch": "main",
                  "language": "TypeScript",
                  "stars": 150000,
                  "forks": 25000,
                  "status": "processing",
                  "task_id": "task-xyz789",
                  "error_message": None,
                  "file_count": 450,
                  "total_size_bytes": 15678900,
                  "languages_breakdown": {
                      "TypeScript": 320,
                      "JavaScript": 80,
                      "CSS": 30
                  },
                  "file_tree": {
                      "type": "folder",
                      "children": {
                          "src": {"type": "folder", "children": {}},
                          "README.md": {"type": "file", "path": "README.md"}
                      }
                  },
                  "created_at": "2025-01-16T10:00:00Z",
                  "updated_at": "2025-01-16T10:05:00Z",
                  "last_fetched": "2025-01-16T10:05:00Z"
              }
          }


  # ==================== File Tree Models ====================

class FileTreeNode(BaseModel):
      """Recursive model for file tree structure."""
      type: str = Field(..., description="Node type: file or folder")
      path: Optional[str] = None
      size: Optional[int] = None
      language: Optional[str] = None
      url: Optional[str] = None
      children: Optional[Dict[str, "FileTreeNode"]] = None

      class Config:
          json_schema_extra = {
              "example": {
                  "type": "folder",
                  "children": {
                      "src": {
                          "type": "folder",
                          "children": {
                              "main.py": {
                                  "type": "file",
                                  "path": "src/main.py",
                                  "size": 1234,
                                  "language": "python"
                              }
                          }
                      }
                  }
              }
          }

  # Rebuild model to resolve forward references (for recursive children field)
FileTreeNode.model_rebuild()