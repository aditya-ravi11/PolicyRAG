from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0
    metadata: dict = field(default_factory=dict)


class BaseLLMProvider(ABC):
    provider_name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        """Generate a response from the LLM."""

    @abstractmethod
    async def generate_with_context(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate a RAG response with numbered context chunks."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available."""
