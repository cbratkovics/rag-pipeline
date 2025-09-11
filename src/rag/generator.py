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


class StubLLM(BaseLLM):
    """Stub LLM that returns deterministic templated answers."""

    def generate(self, prompt: str, contexts: list[str]) -> str:
        """Generate a templated answer using the provided contexts."""
        if not contexts:
            return f"I cannot find relevant information to answer: '{prompt}'"

        # Use the most relevant context (first one)
        top_context = contexts[0][:200] if contexts[0] else ""

        # Create a deterministic template response
        answer = f"Based on the available information, regarding '{prompt}': {top_context}"

        if len(contexts) > 1:
            answer += f" (Found {len(contexts)} relevant sources)"

        return answer


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
            # Fallback to stub response
            return StubLLM().generate(prompt, contexts)


def get_llm(provider: str | None = None) -> BaseLLM:
    """
    Factory function to get the appropriate LLM.

    Args:
        provider: LLM provider name ("stub", "openai")

    Returns:
        LLM instance
    """
    provider = provider or os.getenv("LLM_PROVIDER", "stub")

    if provider == "stub":
        logger.info("Using StubLLM")
        return StubLLM()

    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OpenAI API key not found, falling back to StubLLM")
            return StubLLM()

        try:
            logger.info("Using OpenAI LLM")
            return OpenAILLM(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI LLM: {e}, falling back to StubLLM")
            return StubLLM()

    else:
        logger.warning(f"Unknown provider {provider}, using StubLLM")
        return StubLLM()
