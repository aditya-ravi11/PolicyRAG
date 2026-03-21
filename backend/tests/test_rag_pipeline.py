import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from policyrag.core.rag_pipeline import RAGPipeline
from policyrag.schemas.query import QueryRequest


@pytest.mark.asyncio
async def test_rag_pipeline_basic(mock_llm, sample_chunks):
    with patch("policyrag.core.rag_pipeline.retrieve", new_callable=AsyncMock) as mock_retrieve, \
         patch("policyrag.core.rag_pipeline.LLMFactory") as MockFactory:

        mock_retrieve.return_value = sample_chunks
        MockFactory.create.return_value = mock_llm
        MockFactory.get_active.return_value = ("mock", "mock-model")

        pipeline = RAGPipeline(eval_engine=None)
        request = QueryRequest(query="What was Apple's revenue?")
        response = await pipeline.query(request)

        assert response.query_id
        assert response.answer
        assert response.metadata.provider == "mock"
        assert len(response.source_chunks) > 0


@pytest.mark.asyncio
async def test_rag_pipeline_with_document_filter(mock_llm, sample_chunks):
    with patch("policyrag.core.rag_pipeline.retrieve", new_callable=AsyncMock) as mock_retrieve, \
         patch("policyrag.core.rag_pipeline.LLMFactory") as MockFactory:

        mock_retrieve.return_value = sample_chunks
        MockFactory.create.return_value = mock_llm
        MockFactory.get_active.return_value = ("mock", "mock-model")

        pipeline = RAGPipeline(eval_engine=None)
        request = QueryRequest(query="Revenue?", document_ids=["doc1"])
        response = await pipeline.query(request)

        # Verify retrieve was called with document_ids
        call_kwargs = mock_retrieve.call_args.kwargs
        assert call_kwargs.get("document_ids") == ["doc1"]


@pytest.mark.asyncio
async def test_rag_pipeline_with_eval(mock_llm, sample_chunks):
    with patch("policyrag.core.rag_pipeline.retrieve", new_callable=AsyncMock) as mock_retrieve, \
         patch("policyrag.core.rag_pipeline.LLMFactory") as MockFactory:

        mock_retrieve.return_value = sample_chunks
        MockFactory.create.return_value = mock_llm
        MockFactory.get_active.return_value = ("mock", "mock-model")

        mock_eval = MagicMock()
        from policyrag.schemas.evaluation import EvaluationResult
        mock_eval.evaluate = AsyncMock(return_value=EvaluationResult(
            faithfulness_score=0.9,
            citation_precision=0.85,
            citation_recall=0.8,
            context_relevance=0.7,
            hallucination_score=0.1,
            completeness_score=0.8,
            overall_trust_score=0.82,
            num_claims=5,
            num_faithful_claims=4,
        ))

        pipeline = RAGPipeline(eval_engine=mock_eval)
        request = QueryRequest(query="What was Apple's revenue?")
        response = await pipeline.query(request)

        assert response.evaluation.faithfulness == 0.9
        assert response.evaluation.hallucination_score == 0.1
