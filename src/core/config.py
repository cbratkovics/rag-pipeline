"""Configuration management for the RAG pipeline."""

from functools import lru_cache
from typing import Any

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = Field(default="rag-pipeline-ragas")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # API
    api_host: str = Field(
        default="127.0.0.1"
    )  # Use localhost for security, can be overridden via env
    api_port: int = Field(default=8000)
    api_key_header: str = Field(default="X-API-Key")
    cors_origins: list[str] = Field(default=["*"])

    # Database
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="rag_pipeline")
    postgres_user: str = Field(default="rag_user")
    postgres_password: str = Field(default="password")
    database_url: PostgresDsn | None = None

    # Redis
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_password: str | None = Field(default=None)
    redis_db: int = Field(default=0)
    redis_url: RedisDsn | None = None

    # Vector Store
    vector_store_type: str = Field(default="qdrant")
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_api_key: str | None = Field(default=None)
    qdrant_collection: str = Field(default="rag_documents")
    chromadb_host: str = Field(default="localhost")
    chromadb_port: int = Field(default=8000)
    chromadb_collection: str = Field(default="rag_documents")

    # Embedding Model
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    embedding_dimension: int = Field(default=384)
    embedding_batch_size: int = Field(default=32)

    # LLM
    llm_provider: str = Field(default="openai")
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default="gpt-3.5-turbo")
    anthropic_api_key: str | None = Field(default=None)
    anthropic_model: str = Field(default="claude-3-haiku-20240307")
    local_llm_url: str | None = Field(default=None)
    local_llm_model: str = Field(default="llama2-7b")

    # Reranking
    reranker_model: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2")
    reranker_top_k: int = Field(default=10)

    # Search
    hybrid_search_alpha: float = Field(default=0.5, ge=0.0, le=1.0)
    bm25_k1: float = Field(default=1.2)
    bm25_b: float = Field(default=0.75)
    search_top_k: int = Field(default=20)
    final_top_k: int = Field(default=5)

    # RAG
    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=50)
    max_context_length: int = Field(default=2048)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512)

    # A/B Testing
    ab_test_enabled: bool = Field(default=True)
    ab_test_variants: list[str] = Field(default=["baseline", "reranked", "hybrid", "finetuned"])
    ab_test_default_variant: str = Field(default="baseline")
    ab_test_traffic_split: list[float] = Field(default=[0.25, 0.25, 0.25, 0.25])
    ab_test_min_samples: int = Field(default=100)
    ab_test_confidence_level: float = Field(default=0.95)

    # RAGAS Evaluation
    ragas_enabled: bool = Field(default=True)
    ragas_metrics: list[str] = Field(
        default=[
            "context_relevancy",
            "answer_faithfulness",
            "answer_relevancy",
            "context_recall",
        ]
    )
    ragas_threshold_context_relevancy: float = Field(default=0.8)
    ragas_threshold_answer_faithfulness: float = Field(default=0.8)
    ragas_threshold_answer_relevancy: float = Field(default=0.8)
    ragas_threshold_context_recall: float = Field(default=0.7)

    # Monitoring
    prometheus_enabled: bool = Field(default=True)
    prometheus_port: int = Field(default=9090)
    grafana_enabled: bool = Field(default=True)
    grafana_port: int = Field(default=3000)
    opentelemetry_enabled: bool = Field(default=True)
    otel_exporter_otlp_endpoint: str = Field(default="http://localhost:4317")
    otel_service_name: str = Field(default="rag-pipeline")

    # MLflow
    mlflow_tracking_uri: str = Field(default="http://localhost:5000")
    mlflow_experiment_name: str = Field(default="rag-pipeline-experiments")
    mlflow_artifact_location: str = Field(default="./mlruns")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests_per_minute: int = Field(default=60)
    rate_limit_requests_per_hour: int = Field(default=1000)
    rate_limit_requests_per_day: int = Field(default=10000)

    # Security
    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=24)
    bcrypt_rounds: int = Field(default=12)

    # Data Sources
    arxiv_enabled: bool = Field(default=True)
    wikipedia_enabled: bool = Field(default=True)
    common_crawl_enabled: bool = Field(default=False)
    sec_edgar_enabled: bool = Field(default=False)
    pubmed_enabled: bool = Field(default=False)

    # Feedback
    feedback_enabled: bool = Field(default=True)
    feedback_min_score: int = Field(default=1)
    feedback_max_score: int = Field(default=5)
    feedback_retraining_threshold: int = Field(default=100)
    feedback_negative_threshold: float = Field(default=0.3)

    # Performance
    max_workers: int = Field(default=4)
    connection_pool_size: int = Field(default=20)
    request_timeout_seconds: int = Field(default=30)
    background_task_timeout_seconds: int = Field(default=300)

    # Cache
    cache_ttl_seconds: int = Field(default=3600)
    cache_max_size: int = Field(default=1000)

    # Feature Flags
    feature_query_expansion: bool = Field(default=True)
    feature_metadata_filtering: bool = Field(default=True)
    feature_dynamic_chunking: bool = Field(default=True)
    feature_online_learning: bool = Field(default=False)
    feature_cost_tracking: bool = Field(default=True)

    # Cost Tracking
    cost_per_embedding_request: float = Field(default=0.0001)
    cost_per_llm_token: float = Field(default=0.000002)
    cost_per_rerank_request: float = Field(default=0.00005)
    cost_per_vector_search: float = Field(default=0.00001)

    # Deployment
    deployment_environment: str = Field(default="development")
    deployment_region: str = Field(default="us-west-2")
    deployment_version: str = Field(default="0.1.0")

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, info: Any) -> Any:
        """Construct database URL from components."""
        if isinstance(v, str):
            return v
        values = info.data
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("postgres_user"),
            password=values.get("postgres_password"),
            host=values.get("postgres_host"),
            port=values.get("postgres_port"),
            path=values.get("postgres_db"),
        )

    @field_validator("redis_url", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: str | None, info: Any) -> Any:
        """Construct Redis URL from components."""
        if isinstance(v, str):
            return v
        values = info.data
        password = values.get("redis_password")
        if password:
            return f"redis://:{password}@{values.get('redis_host')}:{values.get('redis_port')}/{values.get('redis_db')}"
        return f"redis://{values.get('redis_host')}:{values.get('redis_port')}/{values.get('redis_db')}"

    @field_validator("ab_test_traffic_split")
    @classmethod
    def validate_traffic_split(cls, v: list[float]) -> list[float]:
        """Ensure traffic split sums to 1.0."""
        if abs(sum(v) - 1.0) > 0.001:
            raise ValueError("A/B test traffic split must sum to 1.0")
        return v

    def get_vector_store_config(self) -> dict[str, Any]:
        """Get vector store configuration based on type."""
        if self.vector_store_type == "qdrant":
            return {
                "type": "qdrant",
                "host": self.qdrant_host,
                "port": self.qdrant_port,
                "api_key": self.qdrant_api_key,
                "collection": self.qdrant_collection,
            }
        elif self.vector_store_type == "chromadb":
            return {
                "type": "chromadb",
                "host": self.chromadb_host,
                "port": self.chromadb_port,
                "collection": self.chromadb_collection,
            }
        else:
            raise ValueError(f"Unknown vector store type: {self.vector_store_type}")

    def get_llm_config(self) -> dict[str, Any]:
        """Get LLM configuration based on provider."""
        base_config = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        if self.llm_provider == "openai":
            return {
                **base_config,
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_model,
            }
        elif self.llm_provider == "anthropic":
            return {
                **base_config,
                "provider": "anthropic",
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model,
            }
        elif self.llm_provider == "local":
            return {
                **base_config,
                "provider": "local",
                "url": self.local_llm_url,
                "model": self.local_llm_model,
            }
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
