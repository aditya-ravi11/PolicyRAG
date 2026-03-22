import logging
import re

from policyrag.core.citation_extractor import ExtractionResult
from policyrag.schemas.evaluation import EvaluationResult
from policyrag.schemas.query import EvaluationScores, QueryMetadata, QueryResponse

logger = logging.getLogger(__name__)

ABSTENTION_TRUST_THRESHOLD = 0.50
ABSTENTION_FAITH_THRESHOLD = 0.30

# Patterns indicating the LLM itself found insufficient info
_NO_INFO_PATTERNS = [
    r"(?:do(?:es)? not|doesn't|don't)\s+(?:contain|provide|include|mention|have|address|discuss)",
    r"no\s+(?:information|data|mention|details?|evidence)\s+(?:about|regarding|on|for|of|provided|available)",
    r"(?:not\s+(?:mentioned|addressed|discussed|covered|available|provided|found))",
    r"(?:cannot|can't|unable to)\s+(?:find|determine|answer|provide|identify)",
    r"(?:insufficient|no sufficient|no relevant)\s+(?:information|data|evidence|context)",
    r"(?:beyond|outside)\s+(?:the\s+)?(?:scope|provided|available)\s+(?:of|context|information|data)",
]
_NO_INFO_RE = re.compile("|".join(_NO_INFO_PATTERNS), re.IGNORECASE)


_DATA_PATTERNS = re.compile(
    r"\$[\d,]+|[\d,]+\s*(?:million|billion|%)|increased|decreased|grew|declined",
    re.IGNORECASE,
)


def _answer_indicates_no_info(answer: str) -> bool:
    """Detect if the LLM's answer indicates it could not find the requested information.

    Distinguishes a true 'no data' answer from a hedging preamble followed by
    actual data (e.g. "The context doesn't provide a direct comparison, but
    net sales were $391B...").
    """
    prefix = answer[:400].lower()
    if not _NO_INFO_RE.search(prefix):
        return False

    # If the rest of the answer contains concrete financial data, the LLM
    # was just hedging — treat it as a real answer, not an abstention.
    remainder = answer[200:]
    if _DATA_PATTERNS.search(remainder):
        return False

    return True


def _should_abstain(evaluation: EvaluationResult | None, answer: str = "") -> bool:
    """Check if the system should abstain from showing the answer."""
    # Content-based: LLM itself says it can't answer
    if _answer_indicates_no_info(answer):
        return True
    if not evaluation:
        return False
    if evaluation.overall_trust_score < ABSTENTION_TRUST_THRESHOLD:
        return True
    if evaluation.faithfulness_score < ABSTENTION_FAITH_THRESHOLD:
        return True
    return False


def _build_abstention_message(
    query: str,
    extraction: ExtractionResult,
) -> str:
    """Build a human-readable abstention message."""
    # Summarize what topics the retrieved chunks covered
    sections = set()
    for chunk in extraction.source_chunks[:5]:
        if chunk.section:
            sections.add(chunk.section)
    section_hint = ", ".join(sorted(sections)[:3]) if sections else "various sections"

    return (
        f"I don't have sufficient information to answer this question reliably.\n\n"
        f"The most relevant sections I found were from {section_hint}, "
        f"which may not directly address your question.\n\n"
        f"Try rephrasing your question, or check that the relevant document sections "
        f"have been uploaded."
    )


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

    # Check abstention
    abstained = _should_abstain(evaluation, answer)
    if abstained:
        content_based = _answer_indicates_no_info(answer)
        trust = evaluation.overall_trust_score if evaluation else 0
        faith = evaluation.faithfulness_score if evaluation else 0
        reason = "llm_no_info" if content_based else "low_scores"
        logger.info(
            f"Abstaining from query ({reason}): trust={trust:.2f}, faith={faith:.2f}",
            extra={
                "stage": "abstention",
                "query_id": query_id,
                "reason": reason,
                "trust_score": trust,
                "faithfulness": faith,
            },
        )
        answer = _build_abstention_message(query, extraction)

    return QueryResponse(
        query_id=query_id,
        query=query,
        answer=answer,
        abstained=abstained,
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
