import pytest
from unittest.mock import patch, MagicMock
import numpy as np

from policyrag.core.retriever import RetrievedChunk


@pytest.fixture
def context_chunks():
    return [
        RetrievedChunk(
            chunk_id="c1",
            text="Apple's total revenue in 2023 was $383.3 billion.",
            score=0.9,
            metadata={},
        ),
        RetrievedChunk(
            chunk_id="c2",
            text="Services revenue grew 9% year-over-year to $85.2 billion.",
            score=0.8,
            metadata={},
        ),
    ]


@pytest.mark.asyncio
async def test_faithfulness_all_faithful(mock_llm, context_chunks):
    mock_llm.responses["claims"] = "1. Apple's revenue was $383.3 billion\n2. Services grew 9%"

    with patch("policyrag.evaluation.faithfulness._get_nli_model") as mock_nli:
        nli = MagicMock()
        # Return entailment scores (label 2 = entailment)
        nli.predict.return_value = [np.array([0.1, 0.1, 0.8]), np.array([0.1, 0.1, 0.8])]
        mock_nli.return_value = nli

        from policyrag.evaluation.faithfulness import evaluate_faithfulness
        result = await evaluate_faithfulness("Answer text", context_chunks, mock_llm)

        assert result.score == 1.0
        assert result.num_claims == 2
        assert result.num_faithful == 2


@pytest.mark.asyncio
async def test_faithfulness_partial(mock_llm, context_chunks):
    mock_llm.responses["claims"] = "1. Revenue was $383B\n2. Revenue grew 50%"

    with patch("policyrag.evaluation.faithfulness._get_nli_model") as mock_nli:
        nli = MagicMock()
        # First entailed, second contradicted
        nli.predict.return_value = [np.array([0.1, 0.1, 0.8]), np.array([0.8, 0.1, 0.1])]
        mock_nli.return_value = nli

        from policyrag.evaluation.faithfulness import evaluate_faithfulness
        result = await evaluate_faithfulness("Answer text", context_chunks, mock_llm)

        assert result.score == 0.5
        assert result.num_faithful == 1


@pytest.mark.asyncio
async def test_faithfulness_no_claims(mock_llm, context_chunks):
    mock_llm.responses["claims"] = ""

    from policyrag.evaluation.faithfulness import evaluate_faithfulness
    result = await evaluate_faithfulness("Short.", context_chunks, mock_llm)
    assert result.score == 1.0
    assert result.num_claims == 0
