import logging
import re
from typing import Optional

from policyrag.core.retriever import RetrievedChunk
from policyrag.evaluation.citation_metrics import evaluate_citation_metrics
from policyrag.evaluation.faithfulness import evaluate_faithfulness
from policyrag.evaluation.relevance import evaluate_context_relevance
from policyrag.llm.base import BaseLLMProvider
from policyrag.llm.prompts import COMPLETENESS_EVALUATION_PROMPT
from policyrag.schemas.citation import Citation
from policyrag.schemas.evaluation import EvaluationResult

logger = logging.getLogger(__name__)


class EvaluationEngine:
    async def evaluate(
        self,
        query: str,
        answer: str,
        context_chunks: list[RetrievedChunk],
        source_map: dict[int, RetrievedChunk],
        citations: list[Citation],
        llm: BaseLLMProvider,
    ) -> EvaluationResult:
        # Faithfulness
        faith_result = await evaluate_faithfulness(answer, context_chunks, llm)

        # Context relevance
        context_relevance = await evaluate_context_relevance(query, context_chunks)

        # Citation metrics (includes per-citation faithfulness verdicts)
        citation_precision, citation_recall, per_citation_faithful = await evaluate_citation_metrics(
            answer, citations, source_map
        )

        # Map per-citation faithfulness back to Citation objects
        for cit in citations:
            if cit.index in per_citation_faithful:
                cit.is_faithful = per_citation_faithful[cit.index]

        # Completeness (LLM-as-judge)
        completeness = await self._evaluate_completeness(query, answer, context_chunks, llm)

        # Composite scores
        hallucination_score = 1.0 - faith_result.score
        overall_trust = (
            faith_result.score * 0.4
            + citation_precision * 0.2
            + citation_recall * 0.1
            + context_relevance * 0.15
            + completeness * 0.15
        )

        return EvaluationResult(
            faithfulness_score=round(faith_result.score, 3),
            citation_precision=round(citation_precision, 3),
            citation_recall=round(citation_recall, 3),
            context_relevance=round(context_relevance, 3),
            hallucination_score=round(hallucination_score, 3),
            completeness_score=round(completeness, 3),
            overall_trust_score=round(overall_trust, 3),
            num_claims=faith_result.num_claims,
            num_faithful_claims=faith_result.num_faithful,
        )

    async def _evaluate_completeness(
        self,
        query: str,
        answer: str,
        chunks: list[RetrievedChunk],
        llm: BaseLLMProvider,
    ) -> float:
        context = "\n".join(c.text[:500] for c in chunks[:5])
        prompt = COMPLETENESS_EVALUATION_PROMPT.format(query=query, context=context, answer=answer)
        try:
            response = await llm.generate(prompt)
            # Extract float from response
            match = re.search(r"(\d+\.?\d*)", response.content)
            if match:
                score = float(match.group(1))
                return min(max(score, 0.0), 1.0)
        except Exception as e:
            logger.warning(f"Completeness evaluation failed: {e}")
        return 0.5
