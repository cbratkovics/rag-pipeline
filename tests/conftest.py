"""Test configuration and fixtures."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment
os.environ.setdefault("LLM_PROVIDER", "stub")
os.environ.setdefault("RAGAS_ENABLED", "false")
os.environ.setdefault("VECTOR_STORE_TYPE", "chromadb")
os.environ.setdefault("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "test_db")
os.environ.setdefault("POSTGRES_USER", "test_user")
os.environ.setdefault("POSTGRES_PASSWORD", "test_password")

# Set protobuf environment to avoid ChromaDB conflicts
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
