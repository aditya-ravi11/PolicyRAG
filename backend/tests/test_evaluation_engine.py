import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import numpy as np

from policyrag.evaluation.engine import EvaluationEngine
from policyrag.core.retriever import RetrievedChunk
from policyrag.schemas.citation import Citation, SourceChunk


@pytest.fixture
def eval_engine():
    return EvaluationEngine()


@pytest.fixture
def source_map(sample_chunks):
    return {i + 1: c for i, c in enumerate(sample_chunks)}


@pytest.fixture
def citations(sample_chunks):
    return [
        Citation(
            index=1,
            chunk=SourceChunk(
                chunk_id=sample_chunks[0].chunk_id,
                text=sample_chunks[0].text,
                relevance_score=sample_chunks[0].score,
            ),
        ),
    ]


@pytest.mark.asyncio
async def test_evaluation_engine_full(eval_engine, mock_llm, sample_chunks, source_map, citations):
    with patch("policyrag.evaluation.faithfulness._get_nli_model") as mock_nli_faith, \
         patch("policyrag.evaluation.citation_metrics._get_nli_model") as mock_nli_cite, \
         patch("policyrag.evaluation.relevance.embed_query", new_callable=AsyncMock) as mock_eq, \
         patch("policyrag.evaluation.relevance.embed_texts", new_callable=AsyncMock) as mock_et:

        # Mock NLI model
        nli = MagicMock()
        nli.predict.return_value = [np.array([0.1, 0.1, 0.8]), np.array([0.1, 0.1, 0.8])]
        mock_nli_faith.return_value = nli
        mock_nli_cite.return_value = nli

        # Mock embeddings
        mock_eq.return_value = [0.1] * 384
        mock_et.return_value = [[0.1] * 384] * len(sample_chunks)

        result = await eval_engine.evaluate(
            query="What was Apple's revenue?",
            answer="Revenue was $383B [1]. Products were $298B [2].",
            context_chunks=sample_chunks,
            source_map=source_map,
            citations=citations,
            llm=mock_llm,
        )

        assert result.faithfulness_score is not None
        assert result.hallucination_score is not None
        assert result.overall_trust_score is not None
        assert 0 <= result.faithfulness_score <= 1
        assert 0 <= result.hallucination_score <= 1
