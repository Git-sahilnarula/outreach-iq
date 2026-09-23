from app.ai.base import AIProvider
from app.ai.ollama_provider import OllamaProvider
from app.config import settings

def get_ai_provider() -> AIProvider:
    """Factory function to get the configured AI provider"""
    if settings.AI_PROVIDER.lower() == "ollama":
        return OllamaProvider()
    else:
        raise ValueError(f"Unsupported AI provider: {settings.AI_PROVIDER}")
