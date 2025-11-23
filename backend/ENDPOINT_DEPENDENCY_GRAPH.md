# Dependency Graph Endpoint

## Overview
New endpoint for retrieving dependency graph data in a format suitable for D3.js visualization.

## Endpoint

```
GET /api/repositories/{repo_id}/dependency-graph
```

## Response Format

```json
{
  "repo_id": "repo-xxx",
  "nodes": [
    {
      "id": "file-uuid",
      "path": "src/app.ts",
      "filename": "app.ts",
      "language": "typescript",
      "functions": ["parseCommand", "handleInput"],
      "classes": ["RedisParser"],
      "has_external_dependencies": true
    }
  ],
  "edges": [
    {
      "source": "file-uuid-1",
      "target": "file-uuid-2",
      "type": "imports"
    }
  ],
  "total_nodes": 45,
  "total_edges": 67
}
```

## Node Properties

- **id**: File UUID (unique identifier)
- **path**: Full file path within repository
- **filename**: File name only
- **language**: Programming language (e.g., "typescript", "python")
- **functions**: Array of function names found in the file
- **classes**: Array of class names found in the file
- **has_external_dependencies**: Boolean indicating if file imports external packages

## Edge Properties

- **source**: Source file UUID (file that imports)
- **target**: Target file UUID (file being imported)
- **type**: Always "imports" for now (can be extended for other relationship types)

## Features

1. **All Files Included**: Returns all files in the repository (parseable and non-parseable)
2. **Internal Dependencies Only**: Edges represent only internal file dependencies (no external packages like `express`, `React`, etc.)
3. **External Dependency Flag**: Each node has a boolean flag indicating if it uses external packages
4. **Function & Class Names**: Nodes include lists of function and class names for richer visualization

## Implementation Details

### Files Modified

1. **backend/app/controllers/repository.py**
   - Added `get_dependency_graph(repo_id)` method (lines 331-429)
   - Fetches all files (up to 10,000 limit)
   - Builds nodes array with metadata
   - Builds edges array from `dependencies.imports` field

2. **backend/app/routers/repository.py**
   - Added route `GET /{repo_id}/dependency-graph` (lines 41-81)
   - Includes comprehensive documentation

### Data Flow

1. Fetch all files for repository from database
2. Build two helper maps:
   - `file_id_to_path`: Maps file IDs to paths
   - `path_to_file_id`: Maps paths to file IDs (for dependency resolution)
3. For each file:
   - Extract function names from `functions` array
   - Extract class names from `classes` array
   - Check if `external_imports` array has entries
   - Add node to array
4. For each file's `dependencies.imports` list:
   - Resolve path to file ID
   - Create edge from source to target
5. Return graph structure

## Usage Example

```bash
# Get dependency graph for a repository
curl http://localhost:8000/api/repositories/repo-123/dependency-graph
```

## Frontend Integration

This endpoint is designed for D3.js force-directed graph visualization:

```javascript
fetch(`/api/repositories/${repoId}/dependency-graph`)
  .then(res => res.json())
  .then(data => {
    // data.nodes = array of file nodes
    // data.edges = array of dependency edges
    // Ready to use with D3.js force simulation
  });
```

## Performance

- Uses MongoDB projection to exclude heavy fields (content, embeddings)
- Efficient lookups using dictionary mappings
- Handles repositories with thousands of files (10,000 file limit)
