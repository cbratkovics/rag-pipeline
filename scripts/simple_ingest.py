#!/usr/bin/env python3
"""Simplified ingestion script for testing."""

import os
import json
from pathlib import Path
import chromadb
from chromadb.config import Settings

def main():
    # Create ChromaDB client
    persist_dir = ".chroma"
    client = chromadb.PersistentClient(
        path=persist_dir,
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Reset collection
    collection_name = "rag_documents"
    try:
        client.delete_collection(collection_name)
        print(f"Deleted existing collection: {collection_name}")
    except:
        pass
    
    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Load documents
    data_dir = Path("data/seed")
    documents = []
    ids = []
    metadatas = []
    
    for file_path in data_dir.glob("**/*"):
        if file_path.is_file() and file_path.suffix in [".txt", ".md"]:
            print(f"Loading {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Simple chunking
            chunk_size = 512
            overlap = 50
            start = 0
            chunk_idx = 0
            
            while start < len(content):
                end = min(start + chunk_size, len(content))
                chunk = content[start:end]
                
                doc_id = f"{file_path.stem}_{chunk_idx}"
                documents.append(chunk)
                ids.append(doc_id)
                metadatas.append({
                    "source": str(file_path),
                    "chunk_index": chunk_idx,
                    "filename": file_path.name
                })
                
                chunk_idx += 1
                start = start + chunk_size - overlap if end < len(content) else len(content)
    
    # Add to collection (without embeddings for now)
    if documents:
        # For testing, use simple hash-based embeddings
        import hashlib
        embeddings = []
        for doc in documents:
            # Create a simple 384-dimensional embedding
            hash_obj = hashlib.sha256(doc.encode())
            hash_bytes = hash_obj.digest()
            # Convert to float list (384 dimensions)
            embedding = []
            for i in range(384):
                byte_idx = i % len(hash_bytes)
                value = hash_bytes[byte_idx] / 255.0  # Normalize to [0, 1]
                embedding.append(value)
            embeddings.append(embedding)
        
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"Successfully ingested {len(documents)} document chunks")
        print(f"Collection now contains {collection.count()} documents")
    else:
        print("No documents found to ingest")

if __name__ == "__main__":
    main()