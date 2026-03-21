from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EvaluationResult(BaseModel):
    faithfulness_score: Optional[float] = None
    citation_precision: Optional[float] = None
    citation_recall: Optional[float] = None
    context_relevance: Optional[float] = None
    hallucination_score: Optional[float] = None
    completeness_score: Optional[float] = None
    overall_trust_score: Optional[float] = None
    num_claims: int = 0
    num_faithful_claims: int = 0


class EvalHistoryResponse(BaseModel):
    id: str
    query_id: str
    query_text: str
    answer_text: str
    provider: str
    model: str
    faithfulness_score: Optional[float] = None
    hallucination_score: Optional[float] = None
    citation_precision: Optional[float] = None
    citation_recall: Optional[float] = None
    context_relevance: Optional[float] = None
    overall_trust_score: Optional[float] = None
    completeness_score: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalyticsResponse(BaseModel):
    total_queries: int = 0
    avg_faithfulness: float = 0.0
    avg_hallucination: float = 0.0
    avg_citation_precision: float = 0.0
    avg_citation_recall: float = 0.0
    avg_context_relevance: float = 0.0
    avg_trust_score: float = 0.0
    avg_completeness: float = 0.0
