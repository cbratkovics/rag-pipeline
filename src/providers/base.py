"""Base abstractions for LLM providers."""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class CompletionRequest(BaseModel):
    """Standardized completion request across all providers."""

    prompt: str = Field(..., description="The prompt to generate a completion for")
    contexts: list[str] = Field(default_factory=list, description="Retrieved contexts for RAG")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=512, ge=1, description="Maximum tokens to generate")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    stream: bool = Field(default=False, description="Whether to stream the response")


class CompletionResponse(BaseModel):
    """Standardized completion response across all providers."""

    text: str = Field(..., description="Generated completion text")
    tokens_used: int = Field(..., description="Total tokens consumed (prompt + completion)")
    latency_ms: float = Field(..., description="Completion latency in milliseconds")
    model: str = Field(..., description="Model used for generation")
    cost_usd: float = Field(default=0.0, description="Estimated cost in USD")


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    This abstraction allows the RAG pipeline to support multiple LLM providers
    (OpenAI, Anthropic, local models, etc.) while maintaining a consistent interface.
    """

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Generate a completion for the given request.

        Args:
            request: Standardized completion request

        Returns:
            Standardized completion response

        Raises:
            Exception: Provider-specific errors should be caught and wrapped
        """
        pass

    @abstractmethod
    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost in USD for a given token count.

        Args:
            tokens: Number of tokens (prompt + completion)

        Returns:
            Estimated cost in USD
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name for logging and telemetry."""
        pass
