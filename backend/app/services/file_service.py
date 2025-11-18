from typing import Optional, Dict, List
from datetime import datetime
import uuid
from app.database import db

class FileService:
    """Service for handling file operations in the repository"""

    def __init__(self):
         self.collection_name = "files"

    async def create_file(
          self,
          repo_id: str,
          session_id: str,
          path: str,
          filename: str,
          extension: str,
          language: str,
          size_bytes: int,
          content: str,
          content_hash: str
      ) -> str:
          """
          Create a new file document.

          Args:
              repo_id: Repository ID
              session_id: Session ID (denormalized for faster queries)
              path: File path in repository (e.g., "src/main.py")
              filename: File name (e.g., "main.py")
              extension: File extension (e.g., ".py")
              language: Programming language (e.g., "python")
              size_bytes: File size in bytes
              content: Raw file content
              content_hash: SHA256 hash for deduplication

          Returns:
              file_id: Generated file ID
          """
          database = db.get_database()
          collection = database[self.collection_name]

          file_id = f"file-{str(uuid.uuid4())}"
          now = datetime.now()

          file_doc = {
              "file_id": file_id,
              "repo_id": repo_id,
              "session_id": session_id,
              "path": path,
              "filename": filename,
              "extension": extension,
              "language": language,
              "size_bytes": size_bytes,
              "content_hash": content_hash,
              "content": content,

              # AST parsing results (will be populated later)
              "functions": [],
              "classes": [],
              "imports": [],

              # Dependencies (will be populated after parsing all files)
              "dependencies": {
                  "imports": [],        # Files this file imports
                  "imported_by": [],    # Files that import this file
                  "external_imports": [] # External packages (npm, pip, etc.)
              },

              # Embeddings (will be generated later)
              "embeddings": [],

              # AI-generated analysis (will be generated later)
              "analysis": None,

              # Processing flags
              "parsed": False,
              "embedded": False,
              "analyzed": False,

              # Timestamps
              "created_at": now,
              "updated_at": now
          }

          await collection.insert_one(file_doc)
          return file_id

    async def get_file(self, file_id: str) -> Optional[Dict]:
          """Get file by file_id"""
          database = db.get_database()
          collection = database[self.collection_name]
          return await collection.find_one({"file_id": file_id})

    async def get_file_by_path(self, repo_id: str, path: str) -> Optional[Dict]:
          """Get file by repository ID and path"""
          database = db.get_database()
          collection = database[self.collection_name]
          return await collection.find_one({"repo_id": repo_id, "path": path})

    async def get_files_by_repo(self, repo_id: str, limit: int = 1000) -> List[Dict]:
          """Get all files for a repository"""
          database = db.get_database()
          collection = database[self.collection_name]
          cursor = collection.find({"repo_id": repo_id}).limit(limit)
          return await cursor.to_list(length=limit)

    async def update_parsed_data(
          self,
          file_id: str,
          functions: List[Dict],
          classes: List[Dict],
          imports: List[str]
      ) -> bool:
          """
          Update file with AST parsing results.

          Args:
              file_id: File ID
              functions: List of function definitions
              classes: List of class definitions
              imports: List of import statements

          Returns:
              True if update succeeded
          """
          database = db.get_database()
          collection = database[self.collection_name]

          result = await collection.update_one(
              {"file_id": file_id},
              {
                  "$set": {
                      "functions": functions,
                      "classes": classes,
                      "imports": imports,
                      "parsed": True,
                      "updated_at": datetime.now()
                  }
              }
          )
          return result.modified_count > 0

    async def update_dependencies(
          self,
          file_id: str,
          imports: List[str],
          imported_by: List[str],
          external_imports: List[str]
      ) -> bool:
          """
          Update file dependency information.

          Args:
              file_id: File ID
              imports: List of file paths this file imports
              imported_by: List of file paths that import this file
              external_imports: List of external packages

          Returns:
              True if update succeeded
          """
          database = db.get_database()
          collection = database[self.collection_name]

          result = await collection.update_one(
              {"file_id": file_id},
              {
                  "$set": {
                      "dependencies.imports": imports,
                      "dependencies.imported_by": imported_by,
                      "dependencies.external_imports": external_imports,
                      "updated_at": datetime.now()
                  }
              }
          )
          return result.modified_count > 0

    async def update_embeddings(self, file_id: str, embeddings: List[Dict]) -> bool:
          """
          Update file with generated embeddings.

          Args:
              file_id: File ID
              embeddings: List of embedding objects

          Returns:
              True if update succeeded
          """
          database = db.get_database()
          collection = database[self.collection_name]

          result = await collection.update_one(
              {"file_id": file_id},
              {
                  "$set": {
                      "embeddings": embeddings,
                      "embedded": True,
                      "updated_at": datetime.now()
                  }
              }
          )
          return result.modified_count > 0

    async def update_analysis(self, file_id: str, analysis: Dict) -> bool:
          """
          Update file with AI-generated analysis.

          Args:
              file_id: File ID
              analysis: Analysis object with summary and embedding

          Returns:
              True if update succeeded
          """
          database = db.get_database()
          collection = database[self.collection_name]

          result = await collection.update_one(
              {"file_id": file_id},
              {
                  "$set": {
                      "analysis": analysis,
                      "analyzed": True,
                      "updated_at": datetime.now()
                  }
              }
          )
          return result.modified_count > 0

    async def delete_files_by_repo(self, repo_id: str) -> int:
          """
          Delete all files for a repository.

          Args:
              repo_id: Repository ID

          Returns:
              Number of files deleted
          """
          database = db.get_database()
          collection = database[self.collection_name]

          result = await collection.delete_many({"repo_id": repo_id})
          return result.deleted_count

    async def count_files_by_repo(self, repo_id: str) -> int:
          """Count total files for a repository"""
          database = db.get_database()
          collection = database[self.collection_name]
          return await collection.count_documents({"repo_id": repo_id})

    async def count_parsed_files(self, repo_id: str) -> int:
          """Count how many files have been parsed"""
          database = db.get_database()
          collection = database[self.collection_name]
          return await collection.count_documents({"repo_id": repo_id, "parsed": True})