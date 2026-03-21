import pytest
from unittest.mock import AsyncMock, MagicMock
from policyrag.llm.base import BaseLLMProvider, LLMResponse


class MockLLMProvider(BaseLLMProvider):
    provider_name = "mock"

    def __init__(self, responses=None):
        self.responses = responses or {}
        self.call_count = 0

    async def generate(self, prompt, system_prompt=None, **kwargs):
        self.call_count += 1
        content = self.responses.get("default", "Mock response")
        if "claim" in prompt.lower() or "decompose" in prompt.lower():
            content = self.responses.get("claims", "1. The revenue was $100B\n2. Growth was 10%")
        if "completeness" in prompt.lower():
            content = self.responses.get("completeness", "0.8")
        return LLMResponse(
            content=content, model="mock-model", provider="mock",
            prompt_tokens=10, completion_tokens=20, latency_ms=50,
        )

    async def generate_with_context(self, query, context, system_prompt=None, **kwargs):
        self.call_count += 1
        content = self.responses.get("rag", f"Based on the context, here is the answer [1]. More details [2].")
        return LLMResponse(
            content=content, model="mock-model", provider="mock",
            prompt_tokens=100, completion_tokens=50, latency_ms=200,
        )

    async def health_check(self):
        return True


@pytest.fixture
def mock_llm():
    return MockLLMProvider()


@pytest.fixture
def sample_filing_text():
    return """
ITEM 1. BUSINESS

Apple Inc. designs, manufactures, and markets smartphones, personal computers,
tablets, wearables, and accessories. The Company also sells a variety of related
services. Total net revenue for fiscal year 2023 was $383.3 billion, a decrease
of 3% from $394.3 billion in 2022.

ITEM 1A. RISK FACTORS

The Company's business, reputation, results of operations, financial condition,
and stock price can be affected by a number of factors. Global markets and
macroeconomic conditions could adversely affect the Company's business.

ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION

Revenue decreased 3% during 2023 compared to 2022 due to lower iPhone and
Mac revenue, partially offset by higher Services revenue. Products revenue
was $298.1 billion, a decrease of 4% year-over-year. Services revenue was
$85.2 billion, an increase of 9% year-over-year.

ITEM 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA

Consolidated Statements of Operations for the fiscal year ended September 30, 2023.
Net sales: $383,285 million. Cost of sales: $214,137 million. Gross margin: $169,148 million.
"""


@pytest.fixture
def sample_chunks():
    from policyrag.core.retriever import RetrievedChunk
    return [
        RetrievedChunk(
            chunk_id="doc1_0",
            text="Total net revenue for fiscal year 2023 was $383.3 billion, a decrease of 3% from $394.3 billion in 2022.",
            score=0.95,
            metadata={"doc_id": "doc1", "section": "Item 1 - Business", "page_num": 1, "company": "Apple"},
        ),
        RetrievedChunk(
            chunk_id="doc1_1",
            text="Products revenue was $298.1 billion, a decrease of 4% year-over-year. Services revenue was $85.2 billion, an increase of 9% year-over-year.",
            score=0.88,
            metadata={"doc_id": "doc1", "section": "Item 7 - MD&A", "page_num": 5, "company": "Apple"},
        ),
        RetrievedChunk(
            chunk_id="doc1_2",
            text="Net sales: $383,285 million. Cost of sales: $214,137 million. Gross margin: $169,148 million.",
            score=0.82,
            metadata={"doc_id": "doc1", "section": "Item 8 - Financial Statements", "page_num": 10, "company": "Apple"},
        ),
    ]
