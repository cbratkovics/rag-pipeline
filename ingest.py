import requests
import json

# Your Render API URL
API_URL = "https://rag-pipeline-api-hksb.onrender.com"

# Test data to ingest
documents = [
    {
        "content": "Retrieval-Augmented Generation (RAG) combines large language models with external knowledge retrieval to generate more accurate responses.",
        "metadata": {"source": "intro", "id": "doc1"},
    },
    {
        "content": "Semantic search uses vector embeddings to find documents based on meaning rather than exact keyword matches.",
        "metadata": {"source": "concepts", "id": "doc2"},
    },
    {
        "content": "BM25 is a probabilistic ranking function used for keyword-based document retrieval in information retrieval systems.",
        "metadata": {"source": "algorithms", "id": "doc3"},
    },
    {
        "content": "Hybrid search combines keyword-based (BM25) and semantic (vector) search to leverage the strengths of both approaches.",
        "metadata": {"source": "techniques", "id": "doc4"},
    },
]

# Send ingestion request
response = requests.post(
    f"{API_URL}/api/v1/ingest",
    json={"documents": documents, "reset": True},
    headers={"Content-Type": "application/json"},
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

# Test a query
if response.status_code == 200:
    query_response = requests.post(
        f"{API_URL}/api/v1/query",
        json={"question": "What is hybrid search?"},
        headers={"Content-Type": "application/json"},
    )
    print(f"\nQuery test status: {query_response.status_code}")
    if query_response.status_code == 200:
        result = query_response.json()
        print(f"Answer: {result.get('answer', 'No answer')[:200]}...")
        print(f"Retrieved {len(result.get('contexts', []))} contexts")
