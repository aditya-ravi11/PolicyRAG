import time
from typing import Optional

from openai import AsyncOpenAI

from policyrag.llm.base import BaseLLMProvider, LLMResponse
from policyrag.llm.prompts import RAG_SYSTEM_PROMPT, RAG_USER_TEMPLATE


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        start = time.time()
        response = await self.client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=messages,
            temperature=kwargs.get("temperature", 0.1),
            max_tokens=kwargs.get("max_tokens", 2048),
        )
        latency = (time.time() - start) * 1000

        usage = response.usage
        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            provider=self.provider_name,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
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
            await self.client.models.list()
            return True
        except Exception:
            return False
