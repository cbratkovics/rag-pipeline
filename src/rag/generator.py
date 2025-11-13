"""Legacy generator module - maintained for backward compatibility.

This module provides a synchronous wrapper around the new async provider system.
New code should use `src.providers` directly for better performance.
"""

import asyncio
import logging
import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv

from src.providers import CompletionRequest, get_provider
from src.providers.base import LLMProvider

load_dotenv()

logger = logging.getLogger(__name__)


class BaseLLM(ABC):
    """Base class for LLM implementations.

    DEPRECATED: Use src.providers.LLMProvider instead for new code.
    """

    @abstractmethod
    def generate(self, prompt: str, contexts: list[str]) -> str:
        """Generate an answer given a prompt and contexts."""
        pass


class OpenAILLM(BaseLLM):
    """OpenAI LLM implementation using the new provider system.

    This class maintains backward compatibility with the old synchronous API
    while using the new async provider system under the hood.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize OpenAI LLM.

        Args:
            api_key: OpenAI API key (defaults to environment variable)
            model: Model name (defaults to environment variable)

        Raises:
            ValueError: If API key is not provided
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        # Create the new provider instance
        self._provider: LLMProvider = get_provider(
            provider_name="openai", api_key=self.api_key, model=self.model
        )

    def generate(self, prompt: str, contexts: list[str]) -> str:
        """Generate an answer using OpenAI API.

        This is a synchronous wrapper that maintains backward compatibility.
        For new async code, use the provider directly.

        Args:
            prompt: The question to answer
            contexts: Retrieved context documents

        Returns:
            Generated answer text

        Raises:
            Exception: OpenAI API errors
        """
        # Create completion request
        request = CompletionRequest(
            prompt=prompt, contexts=contexts, temperature=0.7, max_tokens=512
        )

        # Run async completion in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        response = loop.run_until_complete(self._provider.complete(request))
        return response.text


def get_llm() -> OpenAILLM:
    """Get the OpenAI LLM instance.

    DEPRECATED: Use get_provider() from src.providers for new code.

    Returns:
        OpenAILLM instance

    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "This is a production RAG system that requires real LLM capabilities."
        )

    logger.info("Using OpenAI LLM (via new provider system)")
    return OpenAILLM(api_key=api_key, model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"))
