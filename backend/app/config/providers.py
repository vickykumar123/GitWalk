"""
Provider configuration for AI services (embeddings, chat completions).

Uses OpenAI SDK with custom base_url for multi-provider support.
Easy to extend: just add new provider config below.
"""

from typing import Dict

# Standard embedding dimension for all providers
EMBEDDING_DIMENSION = 768


class ProviderConfig:
    """Configuration for AI providers"""

    # Provider configurations: name -> (base_url, default_embedding_model)
    PROVIDERS = {
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "embedding_model": "text-embedding-3-small",
            "description": "OpenAI official API"
        },
        "gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "embedding_model": "text-embedding-004",
            "description": "Google Gemini via OpenAI-compatible API"
        },
        "together": {
            "base_url": "https://api.together.xyz/v1",
            "embedding_model": "togethercomputer/m2-bert-80M-32k-retrieval",  # 768-dim, 32K context
            "description": "Together AI - M2-BERT embeddings (32K context, optimized for code)"
        },
        "fireworks": {
            "base_url": "https://api.fireworks.ai/inference/v1",
            "embedding_model": "nomic-ai/nomic-embed-text-v1.5",  # 768-dim, 8K context
            "description": "Fireworks AI - Nomic embeddings (8K context)"
        },
    }

    @classmethod
    def get_provider_config(cls, provider: str) -> Dict:
        """Get configuration for a provider"""
        provider = provider.lower()
        if provider not in cls.PROVIDERS:
            available = ", ".join(cls.PROVIDERS.keys())
            raise ValueError(
                f"Unknown provider: '{provider}'. Available: {available}"
            )
        return cls.PROVIDERS[provider]

    @classmethod
    def get_base_url(cls, provider: str) -> str:
        """Get base URL for provider"""
        return cls.get_provider_config(provider)["base_url"]

    @classmethod
    def get_embedding_model(cls, provider: str) -> str:
        """Get default embedding model for provider"""
        return cls.get_provider_config(provider)["embedding_model"]

    @classmethod
    def list_providers(cls) -> Dict[str, str]:
        """List all available providers with descriptions"""
        return {
            name: config["description"]
            for name, config in cls.PROVIDERS.items()
        }
