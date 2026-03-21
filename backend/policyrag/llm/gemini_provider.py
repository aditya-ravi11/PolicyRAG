import time
from typing import Optional

import google.generativeai as genai

from policyrag.llm.base import BaseLLMProvider, LLMResponse
from policyrag.llm.prompts import RAG_SYSTEM_PROMPT, RAG_USER_TEMPLATE

GEMINI_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash",
]


class GeminiProvider(BaseLLMProvider):
    provider_name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)
        self.api_key = api_key

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        # Gemini doesn't have a native system prompt in the same API shape,
        # so we prepend it to the user content
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        else:
            full_prompt = prompt

        start = time.time()
        response = await self.model.generate_content_async(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=kwargs.get("temperature", 0.1),
                max_output_tokens=kwargs.get("max_tokens", 2048),
            ),
        )
        latency = (time.time() - start) * 1000

        content = ""
        if response.parts:
            content = response.text

        return LLMResponse(
            content=content,
            model=self.model_name,
            provider=self.provider_name,
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=latency,
        )

    async def generate_with_context(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        sys_prompt = system_prompt or RAG_SYSTEM_PROMPT
        user_prompt = RAG_USER_TEMPLATE.format(context=context, query=query)
        return await self.generate(user_prompt, system_prompt=sys_prompt, **kwargs)

    async def health_check(self) -> bool:
        try:
            genai.configure(api_key=self.api_key)
            models = genai.list_models()
            return any(True for _ in models)
        except Exception:
            return False
