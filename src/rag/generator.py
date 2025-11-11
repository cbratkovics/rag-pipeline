import logging
import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

logger = logging.getLogger(__name__)


class BaseLLM(ABC):
    """Base class for LLM implementations."""

    @abstractmethod
    def generate(self, prompt: str, contexts: list[str]) -> str:
        """Generate an answer given a prompt and contexts."""
        pass


class OpenAILLM(BaseLLM):
    """OpenAI LLM implementation."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        try:
            import openai

            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError as e:
            raise ImportError("openai package not installed") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate(self, prompt: str, contexts: list[str]) -> str:
        """Generate an answer using OpenAI API."""
        # Prepare the context
        context_str = "\n\n".join(contexts[:3])  # Use top 3 contexts

        # Create the system and user messages
        system_message = (
            "You are a helpful assistant that answers questions based on the provided context. "
            "If the context doesn't contain relevant information, say so. "
            "Be concise and factual in your responses."
        )

        user_message = f"""Context:
{context_str}

Question: {prompt}

Answer:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,  # type: ignore[arg-type]
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                max_tokens=512,
            )

            content = response.choices[0].message.content
            if content is None:
                return ""
            return content.strip()

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


def get_llm() -> OpenAILLM:
    """Get the OpenAI LLM instance."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "This is a production RAG system that requires real LLM capabilities."
        )

    logger.info("Using OpenAI LLM")
    return OpenAILLM(api_key=api_key, model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"))
