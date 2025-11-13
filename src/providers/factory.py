"""Factory for creating LLM provider instances."""

from src.infrastructure.logging import get_logger
from src.providers.base import LLMProvider
from src.providers.openai import OpenAIProvider

logger = get_logger(__name__)


def get_provider(
    provider_name: str | None = None, api_key: str | None = None, model: str | None = None
) -> LLMProvider:
    """Factory to get an LLM provider instance.

    Args:
        provider_name: Name of provider ("openai", etc.). Defaults to "openai"
        api_key: Optional API key override
        model: Optional model override

    Returns:
        Configured LLM provider instance

    Raises:
        ValueError: If provider name is unknown

    Example:
        >>> provider = get_provider("openai")
        >>> request = CompletionRequest(prompt="Hello", contexts=[])
        >>> response = await provider.complete(request)
    """
    # Default to OpenAI (production provider)
    if provider_name is None:
        provider_name = "openai"

    provider_name = provider_name.lower()

    if provider_name == "openai":
        logger.info("Creating OpenAI provider")
        return OpenAIProvider(api_key=api_key, model=model)

    # Future providers can be added here:
    # elif provider_name == "anthropic":
    #     return AnthropicProvider(api_key=api_key, model=model)
    # elif provider_name == "local":
    #     return LocalProvider(model_path=model)

    raise ValueError(
        f"Unknown provider: {provider_name}. Supported providers: openai (more coming soon)"
    )
