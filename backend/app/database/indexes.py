
"""
Database indexes for optimal query performance.

Creates indexes on frequently queried fields to avoid full collection scans.
"""


from app.database import db


async def create_indexes():
    """
    Create indexes for all collections.

    Called on application startup to ensure indexes exist.
    """
    database = db.get_database()

    print("\n📊 Creating database indexes...")

    # Files collection indexes
    files_collection = database["files"]
    await files_collection.create_index("file_id", unique=True)
    await files_collection.create_index("repo_id")  # Frequently queried
    await files_collection.create_index([("repo_id", 1), ("path", 1)], unique=True)
    print("  ✅ Files indexes created")

    # Repositories collection indexes
    repos_collection = database["repositories"]
    await repos_collection.create_index("repo_id", unique=True)
    await repos_collection.create_index("session_id")  # Queried on page reload
    await repos_collection.create_index("task_id")
    print("  ✅ Repositories indexes created")

    # Tasks collection indexes
    tasks_collection = database["tasks"]
    await tasks_collection.create_index("task_id", unique=True)
    await tasks_collection.create_index("status")  # For filtering by status
    print("  ✅ Tasks indexes created")

    # Sessions collection indexes
    sessions_collection = database["sessions"]
    await sessions_collection.create_index("session_id", unique=True)
    print("  ✅ Sessions indexes created")

    # Conversations collection indexes
    conversations_collection = database["conversations"]
    await conversations_collection.create_index("conversation_id", unique=True)
    await conversations_collection.create_index([("session_id", 1), ("repo_id", 1)], unique=True)  # One conversation per (session, repo)
    await conversations_collection.create_index("updated_at")  # For sorting by recency
    print("  ✅ Conversations indexes created")

    # Messages collection indexes
    messages_collection = database["messages"]
    await messages_collection.create_index("message_id", unique=True)
    await messages_collection.create_index("conversation_id")  # Frequently queried
    await messages_collection.create_index([("conversation_id", 1), ("sequence_number", 1)])  # For ordered retrieval
    await messages_collection.create_index("timestamp")  # For cleanup/sorting
    print("  ✅ Messages indexes created")

    print("✅ All indexes created successfully!\n")


async def create_vector_search_index():
    """
    Create TWO Atlas Vector Search indexes for embeddings.

    1. summary_index - For file-level summary embeddings (top-level field)
    2. code_index - For code-level embeddings (classes, functions in array)

    Uses MongoDB's createSearchIndex() method.
    """
    database = db.get_database()
    files_collection = database["files"]

    print("\n🔍 Creating Atlas Vector Search indexes...")

    # Index 1: Summary embeddings (top-level field)
    summary_index = {
        "name": "summary_index",
        "type": "vectorSearch",
        "definition": {
            "fields": [
                {
                    "type": "vector",
                    "path": "summary_embedding",  # Top-level field
                    "numDimensions": 768,
                    "similarity": "cosine"  # Auto-normalizes, works with any vector magnitude
                },
                {
                    "type": "filter",
                    "path": "repo_id"
                },
                {
                    "type": "filter",
                    "path": "path"
                },
                {
                    "type": "filter",
                    "path": "language"
                }
            ]
        }
    }

    # Index 2: Code embeddings (array field)
    code_index = {
        "name": "code_index",
        "type": "vectorSearch",
        "definition": {
            "fields": [
                {
                    "type": "vector",
                    "path": "embeddings.embedding",  # Array field
                    "numDimensions": 768,
                    "similarity": "cosine"  # Auto-normalizes, works with any vector magnitude
                },
                {
                    "type": "filter",
                    "path": "embeddings.type"
                },
                {
                    "type": "filter",
                    "path": "repo_id"
                },
                {
                    "type": "filter",
                    "path": "path"
                },
                {
                    "type": "filter",
                    "path": "language"
                }
            ]
        }
    }

    # Create both indexes
    for index_def in [summary_index, code_index]:
        try:
            index_name = index_def["name"]
            result = await files_collection.create_search_index(index_def)

            print(f"✅ {index_name} created successfully!")
            print(f"   Path: {index_def['definition']['fields'][0]['path']}")

        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                print(f"ℹ️  {index_def['name']} already exists")
            else:
                print(f"❌ Error creating {index_def['name']}: {e}")
                print("   Note: Vector search requires MongoDB Atlas (not available in Community Edition)")


async def create_text_search_index():
    """
    Create text search index for keyword matching in hybrid search.

    Indexes fields for full-text search:
    - path: File path (e.g., "app/rdb-parser.ts")
    - summary: File summary text
    - embeddings.name: Class/function names (e.g., "RDBParser", "parseRDBFile")

    Used for fast keyword matching in hybrid search (vector + text).
    """
    database = db.get_database()
    files_collection = database["files"]

    print("\n📝 Creating text search index...")

    try:
        # Create compound text index with weighted fields
        await files_collection.create_index(
            [
                ("path", "text"),           # File path (highest weight)
                ("summary", "text"),        # File summary
                ("embeddings.name", "text") # Code element names
            ],
            name="text_search_index",
            weights={
                "path": 10,           # Highest priority (filename matches)
                "embeddings.name": 5, # Medium priority (class/function names)
                "summary": 1          # Base priority (summary text)
            },
            default_language="english",
            language_override="text_language"  # Prevent using 'language' field (contains prog languages)
        )
        print("✅ Text search index created successfully!")
        print("   Indexed fields: path (weight:10), embeddings.name (weight:5), summary (weight:1)")

    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
            print("ℹ️  text_search_index already exists")
        else:
            print(f"❌ Error creating text search index: {e}")


async def create_all_indexes():
    """
    Create all indexes including regular indexes, vector search, and text search.

    Called on application startup.
    """
    await create_indexes()
    await create_vector_search_index()
    await create_text_search_index()
