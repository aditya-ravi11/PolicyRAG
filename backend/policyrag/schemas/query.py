from typing import Optional
import uuid

from pydantic import BaseModel, Field

from policyrag.schemas.citation import Citation, SourceChunk


class RetrievalConfig(BaseModel):
    top_k: int = 10
    company_filter: Optional[str] = None
    section_filter: Optional[str] = None
    filing_type_filter: Optional[str] = None
    rerank: bool = True


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    document_ids: list[str] = Field(default_factory=list)
    provider: Optional[str] = None
    model: Optional[str] = None
    retrieval_config: RetrievalConfig = Field(default_factory=RetrievalConfig)
    no_cache: bool = False


class EvaluationScores(BaseModel):
    faithfulness: Optional[float] = None
    hallucination_score: Optional[float] = None
    citation_precision: Optional[float] = None
    citation_recall: Optional[float] = None
    context_relevance: Optional[float] = None
    completeness: Optional[float] = None
    overall_trust_score: Optional[float] = None


class QueryMetadata(BaseModel):
    provider: str
    model: str
    num_chunks_retrieved: int = 0
    latency_retrieval_ms: float = 0
    latency_generation_ms: float = 0
    latency_evaluation_ms: float = 0


class QueryResponse(BaseModel):
    query_id: str
    query: str
    answer: str
    abstained: bool = False
    citations: list[Citation]
    source_chunks: list[SourceChunk]
    evaluation: EvaluationScores
    evaluation_status: str = "completed"
    metadata: QueryMetadata


class EvaluationPollResponse(BaseModel):
    status: str
    evaluation: Optional[EvaluationScores] = None
    latency_evaluation_ms: Optional[float] = None


class VanillaResponse(BaseModel):
    answer: str
    latency_ms: float = 0
    provider: str
    model: str


class CompareResponse(BaseModel):
    query: str
    vanilla: VanillaResponse
    policyrag: QueryResponse
