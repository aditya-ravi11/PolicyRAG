import pytest
from unittest.mock import patch

from policyrag.llm.factory import LLMFactory
from policyrag.llm.openai_provider import OpenAIProvider


def test_create_groq_provider():
    with patch("policyrag.llm.groq_provider.AsyncGroq"):
        provider = LLMFactory.create(provider="groq", model="llama-3.3-70b-versatile", api_key="test-key")
        from policyrag.llm.groq_provider import GroqProvider
        assert isinstance(provider, GroqProvider)
        assert provider.model == "llama-3.3-70b-versatile"


def test_create_gemini_provider():
    with patch("policyrag.llm.gemini_provider.genai"):
        provider = LLMFactory.create(provider="gemini", model="gemini-1.5-flash", api_key="test-key")
        from policyrag.llm.gemini_provider import GeminiProvider
        assert isinstance(provider, GeminiProvider)
        assert provider.model_name == "gemini-1.5-flash"


def test_groq_without_key_raises():
    with patch("policyrag.llm.factory.settings") as mock_settings:
        mock_settings.GROQ_API_KEY = None
        mock_settings.DEFAULT_LLM_PROVIDER = "groq"
        mock_settings.DEFAULT_LLM_MODEL = "llama-3.3-70b-versatile"
        with pytest.raises(ValueError, match="API key"):
            LLMFactory.create(provider="groq", model="llama-3.3-70b-versatile")


def test_gemini_without_key_raises():
    with patch("policyrag.llm.factory.settings") as mock_settings:
        mock_settings.GEMINI_API_KEY = None
        mock_settings.DEFAULT_LLM_PROVIDER = "groq"
        mock_settings.DEFAULT_LLM_MODEL = "llama-3.3-70b-versatile"
        with pytest.raises(ValueError, match="API key"):
            LLMFactory.create(provider="gemini", model="gemini-1.5-flash")


def test_create_openai_provider():
    with patch("policyrag.llm.openai_provider.AsyncOpenAI"):
        provider = LLMFactory.create(provider="openai", model="gpt-4o-mini", api_key="test-key")
        assert isinstance(provider, OpenAIProvider)


def test_create_openai_without_key_raises():
    with patch("policyrag.llm.factory.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = None
        mock_settings.DEFAULT_LLM_PROVIDER = "groq"
        mock_settings.DEFAULT_LLM_MODEL = "llama-3.3-70b-versatile"
        with pytest.raises(ValueError, match="API key"):
            LLMFactory.create(provider="openai", model="gpt-4o-mini")


def test_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown"):
        LLMFactory.create(provider="nonexistent", model="x")


def test_set_and_get_active():
    LLMFactory.set_active("groq", "llama-3.3-70b-versatile")
    provider, model = LLMFactory.get_active()
    assert provider == "groq"
    assert model == "llama-3.3-70b-versatile"


def test_register_custom_provider():
    class CustomProvider:
        pass

    LLMFactory.register("custom", CustomProvider)
    assert "custom" in LLMFactory._registry
    # Cleanup
    del LLMFactory._registry["custom"]
