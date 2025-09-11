import logging
import os
from contextlib import suppress
from pathlib import Path

import chromadb
import typer
from chromadb.config import Settings
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer()


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end]
        chunks.append(chunk)
        start = start + chunk_size - overlap if end < text_length else text_length

    return chunks


def load_documents(data_dir: str) -> list[dict]:
    """Load documents from the data directory."""
    documents: list[dict] = []
    data_path = Path(data_dir)

    if not data_path.exists():
        logger.warning(f"Data directory {data_dir} does not exist")
        return documents

    for file_path in data_path.glob("**/*"):
        if file_path.is_file() and file_path.suffix in [".txt", ".md"]:
            logger.info(f"Loading {file_path}")
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                chunks = chunk_text(content)
                for i, chunk in enumerate(chunks):
                    documents.append(
                        {
                            "id": f"{file_path.stem}_{i}",
                            "text": chunk,
                            "metadata": {
                                "source": str(file_path),
                                "chunk_index": i,
                                "filename": file_path.name,
                            },
                        }
                    )
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")

    logger.info(f"Loaded {len(documents)} document chunks")
    return documents


def create_embeddings(documents: list[dict], model_name: str) -> list[list[float]]:
    """Create embeddings for documents."""
    logger.info(f"Creating embeddings with {model_name}")
    model = SentenceTransformer(model_name)

    texts = [doc["text"] for doc in documents]
    embeddings = model.encode(texts, show_progress_bar=True)

    return [emb.tolist() for emb in embeddings]


@app.command()
def ingest(
    data_dir: str = typer.Option("data/seed", help="Directory containing documents"),
    reset: bool = typer.Option(False, help="Reset the vector store before ingesting"),
    persist_dir: str = typer.Option(None, help="Chroma persistence directory"),
    embedding_model: str = typer.Option(None, help="Embedding model name"),
):
    """Ingest documents into Chroma vector store."""

    # Get configuration from environment
    persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", ".chroma")
    embedding_model = embedding_model or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    logger.info(f"Starting ingestion from {data_dir}")
    logger.info(f"Using embedding model: {embedding_model}")
    logger.info(f"Persisting to: {persist_dir}")

    # Initialize Chroma client
    client = chromadb.PersistentClient(
        path=persist_dir, settings=Settings(anonymized_telemetry=False)
    )

    # Get or create collection
    collection_name = "rag_documents"

    if reset:
        logger.info(f"Resetting collection {collection_name}")
        with suppress(Exception):
            client.delete_collection(collection_name)

    collection = client.get_or_create_collection(
        name=collection_name, metadata={"hnsw:space": "cosine"}
    )

    # Load documents
    documents = load_documents(data_dir)

    if not documents:
        logger.warning("No documents found to ingest")
        return

    # Create embeddings
    embeddings = create_embeddings(documents, embedding_model)

    # Store in Chroma
    logger.info("Storing documents in Chroma")

    ids = [doc["id"] for doc in documents]
    texts = [doc["text"] for doc in documents]
    metadatas = [doc["metadata"] for doc in documents]

    collection.add(
        ids=ids,
        embeddings=embeddings,  # type: ignore[arg-type]
        documents=texts,
        metadatas=metadatas,
    )

    logger.info(f"Successfully ingested {len(documents)} document chunks")
    logger.info(f"Collection now contains {collection.count()} documents")


if __name__ == "__main__":
    app()
