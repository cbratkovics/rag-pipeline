"""OpenAI LLM provider implementation."""

import time
from typing import ClassVar

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.infrastructure.logging import get_logger
from src.providers.base import CompletionRequest, CompletionResponse, LLMProvider

logger = get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of the LLM provider.

    This is the production provider for the RAG pipeline. It uses the OpenAI API
    with automatic retries and cost tracking.
    """

    # OpenAI pricing (as of 2024) - should be externalized to config
    PRICING: ClassVar[dict[str, dict[str, float]]] = {
        "gpt-3.5-turbo": {"input": 0.0005 / 1000, "output": 0.0015 / 1000},
        "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
        "gpt-4-turbo": {"input": 0.01 / 1000, "output": 0.03 / 1000},
    }

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: Model name (defaults to settings)

        Raises:
            ValueError: If API key is not provided
        """
        settings = get_settings()

        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model

        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")

        self.client = AsyncOpenAI(api_key=self.api_key)
        logger.info(f"Initialized OpenAI provider with model: {self.model}")

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "openai"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Generate completion using OpenAI API.

        Args:
            request: Completion request with prompt and contexts

        Returns:
            Completion response with generated text and metadata

        Raises:
            Exception: OpenAI API errors (after retries)
        """
        start_time = time.time()

        # Build context string from retrieved documents
        context_str = ""
        if request.contexts:
            context_str = "\n\n".join(request.contexts[:3])  # Use top 3 contexts

        # Construct messages
        system_message = (
            "You are a helpful assistant that answers questions based on the provided context. "
            "If the context doesn't contain relevant information, say so clearly. "
            "Be concise, factual, and cite specific details from the context when possible."
        )

        user_message = f"""Context:
{context_str}

Question: {request.prompt}

Answer:"""

        try:
            # Call OpenAI API (streaming not yet supported)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                stream=False,  # Force non-streaming for now
            )

            # Extract completion
            content = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000

            # Estimate cost
            cost_usd = self.estimate_cost(tokens_used)

            logger.info(
                "OpenAI completion successful",
                model=self.model,
                tokens=tokens_used,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
            )

            return CompletionResponse(
                text=content.strip(),
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                model=self.model,
                cost_usd=cost_usd,
            )

        except Exception as e:
            logger.error(f"OpenAI API error: {e}", model=self.model, exc_info=True)
            raise

    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for OpenAI API call.

        Args:
            tokens: Total tokens (prompt + completion)

        Returns:
            Estimated cost in USD

        Note:
            This is a simplified estimate assuming 50/50 split between input/output tokens.
            Production systems should track actual input/output tokens separately.
        """
        # Get pricing for model (default to gpt-3.5-turbo if not found)
        pricing = self.PRICING.get(self.model, self.PRICING["gpt-3.5-turbo"])

        # Assume 60% input, 40% output split (typical for RAG)
        input_tokens = int(tokens * 0.6)
        output_tokens = int(tokens * 0.4)

        cost = (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])
        return round(cost, 6)
