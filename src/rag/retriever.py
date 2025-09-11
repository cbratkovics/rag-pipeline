import os
import logging
from typing import List, Tuple, Dict, Any, Optional

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Hybrid retriever combining BM25 and vector search."""
    
    def __init__(
        self,
        persist_dir: Optional[str] = None,
        embedding_model: Optional[str] = None,
        collection_name: str = "rag_documents"
    ):
        # Configuration
        self.persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", ".chroma")
        self.embedding_model_name = embedding_model or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,  # type: ignore[arg-type]
            settings=Settings(anonymized_telemetry=False)
        )
        
        try:
            self.collection = self.client.get_collection(collection_name)
        except:
            logger.warning(f"Collection {collection_name} not found. Creating empty collection.")
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        # Cache for BM25
        self._bm25_index: Optional[BM25Okapi] = None
        self._corpus_texts: Optional[List[str]] = None
        self._corpus_ids: Optional[List[str]] = None
        self._corpus_metadata: Optional[List[Dict[str, Any]]] = None
    
    def _build_bm25_index(self):
        """Build BM25 index from collection."""
        if self._bm25_index is not None:
            return
        
        # Get all documents from collection
        results = self.collection.get()
        
        if not results["documents"]:
            logger.warning("No documents in collection for BM25 indexing")
            self._corpus_texts = []
            self._corpus_ids = []
            self._corpus_metadata = []
            self._bm25_index = None
            return
        
        self._corpus_texts = results["documents"]
        self._corpus_ids = results["ids"]
        self._corpus_metadata = results["metadatas"]  # type: ignore[assignment]
        
        # Tokenize documents for BM25
        tokenized_corpus = [doc.lower().split() for doc in self._corpus_texts]
        self._bm25_index = BM25Okapi(tokenized_corpus)
        
        logger.info(f"Built BM25 index with {len(self._corpus_texts)} documents")
    
    def bm25_search(self, query: str, top_k: int = 10) -> List[Tuple[str, str, float, dict]]:
        """
        Perform BM25 search.
        Returns: List of (id, text, score, metadata) tuples
        """
        self._build_bm25_index()
        
        if not self._bm25_index or not self._corpus_texts or not self._corpus_ids:
            return []
        
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get BM25 scores
        scores = self._bm25_index.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((
                    self._corpus_ids[idx],
                    self._corpus_texts[idx],
                    float(scores[idx]),
                    self._corpus_metadata[idx] if self._corpus_metadata else {}
                ))
        
        return results
    
    def vector_search(self, query: str, top_k: int = 10) -> List[Tuple[str, str, float, dict]]:
        """
        Perform vector similarity search.
        Returns: List of (id, text, score, metadata) tuples
        """
        # Create query embedding
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        # Search in Chroma
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        if not results.get("documents") or not results["documents"][0]:  # type: ignore[index]
            return []
        
        # Format results
        formatted_results = []
        for i in range(len(results["documents"][0])):  # type: ignore[index]
            formatted_results.append((
                results["ids"][0][i],
                results["documents"][0][i],  # type: ignore[index]
                1.0 - results["distances"][0][i],  # type: ignore[index]
                results["metadatas"][0][i] if results.get("metadatas") else {}  # type: ignore[index]
            ))
        
        return formatted_results  # type: ignore[return-value]
    
    def rrf_combine(
        self,
        bm25_results: List[Tuple[str, str, float, dict]],
        vector_results: List[Tuple[str, str, float, dict]],
        k: int = 60
    ) -> List[Tuple[str, str, Dict[str, float], dict]]:
        """
        Combine results using Reciprocal Rank Fusion.
        Returns: List of (id, text, scores_dict, metadata) tuples
        """
        # Create dictionaries for easy lookup
        bm25_dict = {r[0]: (r[1], r[2], r[3]) for r in bm25_results}
        vector_dict = {r[0]: (r[1], r[2], r[3]) for r in vector_results}
        
        # Calculate RRF scores
        rrf_scores: Dict[str, float] = {}
        
        # Process BM25 results
        for rank, (doc_id, text, score, metadata) in enumerate(bm25_results):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        
        # Process vector results
        for rank, (doc_id, text, score, metadata) in enumerate(vector_results):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        
        # Sort by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        # Prepare final results
        results = []
        for doc_id in sorted_ids:
            # Get text and metadata from either source
            if doc_id in bm25_dict:
                text, bm25_score, metadata = bm25_dict[doc_id]
            else:
                text, _, metadata = vector_dict[doc_id]
                bm25_score = 0.0
            
            if doc_id in vector_dict:
                _, vector_score, _ = vector_dict[doc_id]
            else:
                vector_score = 0.0
            
            scores = {
                "hybrid": rrf_scores[doc_id],
                "bm25": bm25_score,
                "vector": vector_score
            }
            
            results.append((doc_id, text, scores, metadata))
        
        return results
    
    def weighted_combine(
        self,
        bm25_results: List[Tuple[str, str, float, dict]],
        vector_results: List[Tuple[str, str, float, dict]],
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5
    ) -> List[Tuple[str, str, Dict[str, float], dict]]:
        """
        Combine results using weighted scoring.
        Returns: List of (id, text, scores_dict, metadata) tuples
        """
        # Normalize scores
        max_bm25 = max([r[2] for r in bm25_results], default=1.0)
        max_vector = max([r[2] for r in vector_results], default=1.0)
        
        # Create dictionaries with normalized scores
        bm25_dict = {r[0]: (r[1], r[2]/max_bm25 if max_bm25 > 0 else 0, r[3]) for r in bm25_results}
        vector_dict = {r[0]: (r[1], r[2]/max_vector if max_vector > 0 else 0, r[3]) for r in vector_results}
        
        # Calculate weighted scores
        weighted_scores: Dict[str, float] = {}
        all_docs = {}
        
        for doc_id, (text, score, metadata) in bm25_dict.items():
            weighted_scores[doc_id] = weighted_scores.get(doc_id, 0) + bm25_weight * score
            all_docs[doc_id] = (text, metadata, score, 0.0)
        
        for doc_id, (text, score, metadata) in vector_dict.items():
            weighted_scores[doc_id] = weighted_scores.get(doc_id, 0) + vector_weight * score
            if doc_id in all_docs:
                text, metadata, bm25_score, _ = all_docs[doc_id]
                all_docs[doc_id] = (text, metadata, bm25_score, score)
            else:
                all_docs[doc_id] = (text, metadata, 0.0, score)
        
        # Sort by weighted score
        sorted_ids = sorted(weighted_scores.keys(), key=lambda x: weighted_scores[x], reverse=True)
        
        # Prepare final results
        results = []
        for doc_id in sorted_ids:
            text, metadata, bm25_score, vector_score = all_docs[doc_id]
            
            scores = {
                "hybrid": weighted_scores[doc_id],
                "bm25": bm25_score * max_bm25 if max_bm25 > 0 else 0,
                "vector": vector_score * max_vector if max_vector > 0 else 0
            }
            
            results.append((doc_id, text, scores, metadata))
        
        return results
    
    def retrieve(
        self,
        query: str,
        top_k_bm25: int = 10,
        top_k_vec: int = 10,
        final_k: int = 5,
        fusion_method: str = "rrf",
        rrf_k: int = 60,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5
    ) -> Dict[str, Any]:
        """
        Perform hybrid retrieval.
        
        Args:
            query: Search query
            top_k_bm25: Number of BM25 results to retrieve
            top_k_vec: Number of vector results to retrieve
            final_k: Final number of results to return
            fusion_method: "rrf" or "weighted"
            rrf_k: K parameter for RRF
            bm25_weight: Weight for BM25 in weighted fusion
            vector_weight: Weight for vector search in weighted fusion
        
        Returns:
            Dictionary with contexts, scores, and metadata
        """
        # Perform searches
        bm25_results = self.bm25_search(query, top_k_bm25)
        vector_results = self.vector_search(query, top_k_vec)
        
        # Combine results
        if fusion_method == "rrf":
            combined = self.rrf_combine(bm25_results, vector_results, k=rrf_k)
        else:
            combined = self.weighted_combine(
                bm25_results, vector_results,
                bm25_weight=bm25_weight, vector_weight=vector_weight
            )
        
        # Take top k results
        final_results = combined[:final_k]
        
        # Format output
        contexts = [r[1] for r in final_results]
        scores = {
            "hybrid": [r[2]["hybrid"] for r in final_results],
            "bm25": [r[2]["bm25"] for r in final_results],
            "vector": [r[2]["vector"] for r in final_results]
        }
        metadata = [r[3] for r in final_results]
        
        return {
            "contexts": contexts,
            "scores": scores,
            "metadata": metadata
        }