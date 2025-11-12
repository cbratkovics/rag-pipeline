"""Main RAG pipeline orchestrating retrieval and generation."""

import time
from typing import Any

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from src.core.config import get_settings
from src.core.models import (
    ExperimentVariant,
    Query,
    QueryResult,
    QueryStatus,
    RetrievedDocument,
)
from src.infrastructure.logging import LoggerMixin, get_correlation_id
from src.retrieval.embeddings import embedding_manager
from src.retrieval.hybrid_search import hybrid_searcher, query_expander
from src.retrieval.reranker import reranker
from src.retrieval.vector_store import vector_store


class RAGPipeline(LoggerMixin):
    """Main RAG pipeline for query processing."""

    def __init__(self):
        """Initialize RAG pipeline."""
        self.settings = get_settings()
        self.llm = self._initialize_llm()
        self.prompt_template = self._create_prompt_template()

    def _initialize_llm(self):
        """Initialize the OpenAI language model."""
        llm_config = self.settings.get_llm_config()

        # Production always uses OpenAI - no exceptions
        if not self.settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required. This is a production system that requires real LLM capabilities."
            )

        return ChatOpenAI(
            model=llm_config.get("model", "gpt-3.5-turbo"),
            temperature=llm_config.get("temperature", 0.7),
            api_key=SecretStr(self.settings.openai_api_key)
            if self.settings.openai_api_key
            else None,
        )

    def _create_prompt_template(self) -> PromptTemplate:
        """Create the prompt template for RAG."""
        template = """You are a helpful AI assistant. Use the following context to answer the question.
If you cannot answer the question based on the context, say so.

Context:
{context}

Question: {question}

Answer: """

        return PromptTemplate(
            input_variables=["context", "question"],
            template=template,
        )

    async def process_query(
        self,
        query: Query,
        variant: ExperimentVariant | None = None,
    ) -> QueryResult:
        """Process a query through the RAG pipeline."""
        start_time = time.time()
        variant = variant or query.experiment_variant or ExperimentVariant.BASELINE

        try:
            # Query expansion if enabled
            expanded_query = query.text
            if self.settings.feature_query_expansion and variant != ExperimentVariant.BASELINE:
                expanded_queries = query_expander.expand_query(query.text)
                expanded_query = " ".join(expanded_queries)
                self.logger.debug(
                    "Query expanded",
                    original=query.text,
                    expanded=expanded_query,
                )

            # Retrieve documents based on variant
            retrieved_docs = await self._retrieve_documents(
                query_text=expanded_query,
                variant=variant,
                metadata_filter=query.metadata_filters,
                top_k=query.max_results,
            )

            # Generate answer
            answer, token_count = await self._generate_answer(
                question=query.text,
                documents=retrieved_docs,
                temperature=query.temperature,
                max_tokens=query.max_tokens,
            )

            # Calculate costs
            processing_time = (time.time() - start_time) * 1000
            cost = self._calculate_cost(
                retrieval_count=len(retrieved_docs),
                token_count=token_count,
                variant=variant,
            )

            # Create result
            result = QueryResult(
                query_id=query.id,
                query_text=query.text,
                answer=answer,
                sources=retrieved_docs if query.include_sources else [],
                experiment_variant=variant,
                confidence_score=self._calculate_confidence(retrieved_docs),
                processing_time_ms=processing_time,
                token_count=token_count,
                cost_usd=cost,
                status=QueryStatus.COMPLETED,
            )

            self.logger.info(
                "Query processed successfully",
                query_id=str(query.id),
                variant=variant.value,
                processing_time_ms=processing_time,
                correlation_id=get_correlation_id(),
            )

            return result

        except Exception as e:
            self.logger.error(
                "Query processing failed",
                query_id=str(query.id),
                error=str(e),
                correlation_id=get_correlation_id(),
            )

            return QueryResult(
                query_id=query.id,
                query_text=query.text,
                answer="I encountered an error while processing your query.",
                sources=[],
                experiment_variant=variant,
                confidence_score=0.0,
                processing_time_ms=(time.time() - start_time) * 1000,
                token_count=0,
                cost_usd=0.0,
                status=QueryStatus.FAILED,
                error_message=str(e),
            )

    async def _retrieve_documents(
        self,
        query_text: str,
        variant: ExperimentVariant,
        metadata_filter: dict[str, Any] | None = None,
        top_k: int = 5,
    ) -> list[RetrievedDocument]:
        """Retrieve documents based on variant strategy."""
        if variant == ExperimentVariant.BASELINE:
            # Simple semantic search
            query_embedding = embedding_manager.embed_text(query_text)
            documents = await vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                metadata_filter=metadata_filter,
            )

        elif variant == ExperimentVariant.RERANKED:
            # Semantic search with reranking
            query_embedding = embedding_manager.embed_text(query_text)
            initial_docs = await vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k * 3,  # Get more for reranking
                metadata_filter=metadata_filter,
            )
            documents = reranker.rerank(query_text, initial_docs, top_k=top_k)

        elif variant == ExperimentVariant.HYBRID:
            # Hybrid search with reranking
            initial_docs = await hybrid_searcher.search(
                query=query_text,
                top_k=top_k * 3,
                metadata_filter=metadata_filter,
            )
            documents = reranker.rerank(query_text, initial_docs, top_k=top_k)

        elif variant == ExperimentVariant.FINETUNED:
            # Use fine-tuned embeddings (placeholder for now)
            # In production, this would use a fine-tuned model
            documents = await self._retrieve_documents(
                query_text=query_text,
                variant=ExperimentVariant.HYBRID,
                metadata_filter=metadata_filter,
                top_k=top_k,
            )

        else:
            raise ValueError(f"Unknown experiment variant: {variant}")

        return documents

    async def _generate_answer(
        self,
        question: str,
        documents: list[RetrievedDocument],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> tuple[str, int]:
        """Generate answer using LLM."""
        if not documents:
            return "I couldn't find relevant information to answer your question.", 0

        # Prepare context from documents
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source_info = f"[Source {i}]"
            if doc.document.title:
                source_info += f" {doc.document.title}"
            if doc.document.source:
                source_info += f" ({doc.document.source.value})"
            context_parts.append(f"{source_info}\n{doc.document.content}")

        context = "\n\n".join(context_parts)

        # Truncate context if too long
        max_context = self.settings.max_context_length
        if len(context) > max_context:
            context = context[:max_context] + "..."

        # Update LLM parameters if provided
        if temperature is not None:
            self.llm.temperature = temperature
        if max_tokens is not None:
            self.llm.max_tokens = max_tokens

        # Create chain and generate
        chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

        try:
            response = await chain.ainvoke({"context": context, "question": question})
            answer = response["text"].strip()

            # Estimate token count (rough approximation)
            token_count = len(context.split()) + len(question.split()) + len(answer.split())

            return answer, token_count

        except Exception as e:
            self.logger.error("Answer generation failed", error=str(e))
            return "I encountered an error while generating the answer.", 0

    def _calculate_confidence(self, documents: list[RetrievedDocument]) -> float:
        """Calculate confidence score based on retrieval quality."""
        if not documents:
            return 0.0

        # Average of top document scores
        scores = [doc.score for doc in documents[:3]]  # Top 3
        if not scores:
            return 0.0

        avg_score = sum(scores) / len(scores)

        # Normalize to 0-1 range
        confidence = min(max(avg_score, 0.0), 1.0)

        return round(confidence, 3)

    def _calculate_cost(
        self,
        retrieval_count: int,
        token_count: int,
        variant: ExperimentVariant,
    ) -> float:
        """Calculate cost of query processing."""
        cost = 0.0

        # Embedding cost
        cost += self.settings.cost_per_embedding_request

        # Vector search cost
        cost += self.settings.cost_per_vector_search * retrieval_count

        # Reranking cost if applicable
        if variant in [ExperimentVariant.RERANKED, ExperimentVariant.HYBRID]:
            cost += self.settings.cost_per_rerank_request * retrieval_count

        # LLM token cost
        cost += self.settings.cost_per_llm_token * token_count

        return round(cost, 6)


# Global RAG pipeline instance
rag_pipeline = RAGPipeline()
