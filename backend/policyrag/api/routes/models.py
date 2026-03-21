from fastapi import APIRouter

from policyrag.llm.factory import LLMFactory
from policyrag.llm.groq_provider import GROQ_MODELS
from policyrag.llm.gemini_provider import GEMINI_MODELS
from policyrag.config import settings

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get("")
async def list_models():
    """List available models from all providers."""
    models = []

    # Groq models
    if settings.GROQ_API_KEY:
        for m in GROQ_MODELS:
            models.append({"provider": "groq", "model": m, "available": True})

    # Gemini models
    if settings.GEMINI_API_KEY:
        for m in GEMINI_MODELS:
            models.append({"provider": "gemini", "model": m, "available": True})

    # OpenAI models
    if settings.OPENAI_API_KEY:
        for m in ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]:
            models.append({"provider": "openai", "model": m, "available": True})

    return models


@router.get("/active")
async def get_active():
    provider, model = LLMFactory.get_active()
    return {"provider": provider, "model": model}


@router.post("/switch")
async def switch_model(provider: str, model: str):
    LLMFactory.set_active(provider, model)
    return {"provider": provider, "model": model, "status": "active"}


@router.get("/health")
async def health_check():
    results = {}

    # Check Groq
    if settings.GROQ_API_KEY:
        from policyrag.llm.groq_provider import GroqProvider
        groq_provider = GroqProvider(api_key=settings.GROQ_API_KEY)
        results["groq"] = await groq_provider.health_check()
    else:
        results["groq"] = False

    # Check Gemini
    if settings.GEMINI_API_KEY:
        from policyrag.llm.gemini_provider import GeminiProvider
        gemini_provider = GeminiProvider(api_key=settings.GEMINI_API_KEY)
        results["gemini"] = await gemini_provider.health_check()
    else:
        results["gemini"] = False

    # Check OpenAI
    if settings.OPENAI_API_KEY:
        from policyrag.llm.openai_provider import OpenAIProvider
        openai_provider = OpenAIProvider(api_key=settings.OPENAI_API_KEY)
        results["openai"] = await openai_provider.health_check()
    else:
        results["openai"] = False

    return results
