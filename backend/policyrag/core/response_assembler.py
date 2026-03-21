from policyrag.core.citation_extractor import ExtractionResult
from policyrag.schemas.evaluation import EvaluationResult
from policyrag.schemas.query import EvaluationScores, QueryMetadata, QueryResponse


def assemble_response(
    query_id: str,
    query: str,
    answer: str,
    extraction: ExtractionResult,
    evaluation: EvaluationResult | None,
    provider: str,
    model: str,
    num_chunks: int,
    latency_retrieval_ms: float,
    latency_generation_ms: float,
    latency_evaluation_ms: float,
) -> QueryResponse:
    eval_scores = EvaluationScores()
    if evaluation:
        eval_scores = EvaluationScores(
            faithfulness=evaluation.faithfulness_score,
            hallucination_score=evaluation.hallucination_score,
            citation_precision=evaluation.citation_precision,
            citation_recall=evaluation.citation_recall,
            context_relevance=evaluation.context_relevance,
            completeness=evaluation.completeness_score,
            overall_trust_score=evaluation.overall_trust_score,
        )

    return QueryResponse(
        query_id=query_id,
        query=query,
        answer=answer,
        citations=extraction.citations,
        source_chunks=extraction.source_chunks,
        evaluation=eval_scores,
        metadata=QueryMetadata(
            provider=provider,
            model=model,
            num_chunks_retrieved=num_chunks,
            latency_retrieval_ms=round(latency_retrieval_ms, 1),
            latency_generation_ms=round(latency_generation_ms, 1),
            latency_evaluation_ms=round(latency_evaluation_ms, 1),
        ),
    )
