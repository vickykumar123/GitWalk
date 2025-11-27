"""
Centralized AI model configuration.
Single source of truth for default models per provider.
"""

MODEL_DEFAULTS = {
    "openai": "gpt-4o-mini",
    "gemini": "gemini-1.5-flash",
    "together": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "fireworks": "accounts/fireworks/models/llama-v3p1-70b-instruct",
}

FALLBACK_MODEL = "gpt-4o-mini"


def get_default_model(provider: str) -> str:
    """
    Get default model for a provider.

    Args:
        provider: AI provider name (openai, gemini, together, fireworks)

    Returns:
        Model name string
    """
    return MODEL_DEFAULTS.get(provider, FALLBACK_MODEL)
