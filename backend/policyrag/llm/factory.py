from typing import Optional

from policyrag.config import settings
from policyrag.llm.base import BaseLLMProvider
from policyrag.llm.openai_provider import OpenAIProvider


class LLMFactory:
    _registry: dict[str, type] = {}
    _active_provider: Optional[str] = None
    _active_model: Optional[str] = None

    @classmethod
    def register(cls, name: str, provider_class: type) -> None:
        cls._registry[name] = provider_class

    @classmethod
    def create(cls, provider: Optional[str] = None, model: Optional[str] = None, **kwargs) -> BaseLLMProvider:
        provider = provider or cls._active_provider or settings.DEFAULT_LLM_PROVIDER
        model = model or cls._active_model or settings.DEFAULT_LLM_MODEL

        if provider == "openai":
            api_key = kwargs.get("api_key") or settings.OPENAI_API_KEY
            if not api_key:
                raise ValueError("OpenAI API key not configured")
            return OpenAIProvider(api_key=api_key, model=model)

        if provider == "groq":
            from policyrag.llm.groq_provider import GroqProvider
            api_key = kwargs.get("api_key") or settings.GROQ_API_KEY
            if not api_key:
                raise ValueError("Groq API key not configured")
            return GroqProvider(api_key=api_key, model=model)

        if provider == "gemini":
            from policyrag.llm.gemini_provider import GeminiProvider
            api_key = kwargs.get("api_key") or settings.GEMINI_API_KEY
            if not api_key:
                raise ValueError("Gemini API key not configured")
            return GeminiProvider(api_key=api_key, model=model)

        if provider in cls._registry:
            return cls._registry[provider](model=model, **kwargs)

        raise ValueError(f"Unknown LLM provider: {provider}")

    @classmethod
    def set_active(cls, provider: str, model: str) -> None:
        cls._active_provider = provider
        cls._active_model = model

    @classmethod
    def get_active(cls) -> tuple[str, str]:
        return (
            cls._active_provider or settings.DEFAULT_LLM_PROVIDER,
            cls._active_model or settings.DEFAULT_LLM_MODEL,
        )

    @classmethod
    def available_providers(cls) -> list[dict]:
        providers = []
        if settings.GROQ_API_KEY:
            providers.append({"name": "groq", "description": "Groq (Free)", "requires_key": True})
        if settings.GEMINI_API_KEY:
            providers.append({"name": "gemini", "description": "Google Gemini (Free)", "requires_key": True})
        if settings.OPENAI_API_KEY:
            providers.append({"name": "openai", "description": "OpenAI API", "requires_key": True})
        for name in cls._registry:
            if name not in ("openai", "groq", "gemini"):
                providers.append({"name": name, "description": f"Custom: {name}", "requires_key": False})
        return providers
