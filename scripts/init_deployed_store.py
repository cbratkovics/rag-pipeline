"""One-time initialization script for deployed vector store."""

import os
import sys
from pathlib import Path

import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def initialize_deployed_store():
    """Initialize the deployed vector store with seed documents."""

    # Use production URL or fallback to local
    api_url = os.getenv("API_URL", "https://rag-pipeline-api-hksb.onrender.com")
    endpoint = f"{api_url}/api/v1/admin/initialize"

    print(f"Initializing vector store at: {endpoint}")

    try:
        response = requests.post(
            endpoint, json={"reset": True, "data_dir": "data/seed"}, timeout=30
        )
        response.raise_for_status()
        result = response.json()
        print(f"✓ Vector store initialized: {result}")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return False


if __name__ == "__main__":
    success = initialize_deployed_store()
    sys.exit(0 if success else 1)
