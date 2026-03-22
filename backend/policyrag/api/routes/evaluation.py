import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from policyrag.api.deps import get_db
from policyrag.auth.jwt_verifier import get_current_user
from policyrag.db.repositories.evaluation_repo import EvaluationRepository
from policyrag.schemas.evaluation import AnalyticsResponse, EvalHistoryResponse

router = APIRouter(prefix="/api/v1/evaluation", tags=["evaluation"])


@router.get("/history", response_model=list[EvalHistoryResponse], summary="Evaluation history", description="Retrieve paginated evaluation history, optionally filtered by LLM provider.")
async def get_history(
    limit: int = 50,
    offset: int = 0,
    provider: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    repo = EvaluationRepository(db)
    records = await repo.list_history(limit=limit, offset=offset, provider=provider, user_id=user["user_id"])
    return [
        EvalHistoryResponse(
            id=str(r.id), query_id=str(r.query_id), query_text=r.query_text,
            answer_text=r.answer_text, provider=r.provider, model=r.model,
            faithfulness_score=r.faithfulness_score,
            hallucination_score=r.hallucination_score,
            citation_precision=r.citation_precision,
            citation_recall=r.citation_recall,
            context_relevance=r.context_relevance,
            overall_trust_score=r.overall_trust_score,
            completeness_score=r.completeness_score,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get("/query/{query_id}", response_model=EvalHistoryResponse, summary="Get evaluation by query", description="Retrieve the evaluation result for a specific query ID.")
async def get_by_query(
    query_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    repo = EvaluationRepository(db)
    r = await repo.get_by_query_id(uuid.UUID(query_id), user_id=user["user_id"])
    if not r:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return EvalHistoryResponse(
        id=str(r.id), query_id=str(r.query_id), query_text=r.query_text,
        answer_text=r.answer_text, provider=r.provider, model=r.model,
        faithfulness_score=r.faithfulness_score,
        hallucination_score=r.hallucination_score,
        citation_precision=r.citation_precision,
        citation_recall=r.citation_recall,
        context_relevance=r.context_relevance,
        overall_trust_score=r.overall_trust_score,
        completeness_score=r.completeness_score,
        created_at=r.created_at,
    )


@router.get("/analytics", response_model=AnalyticsResponse, summary="Evaluation analytics", description="Get aggregate evaluation metrics across all queries, optionally filtered by provider.")
async def get_analytics(
    provider: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    repo = EvaluationRepository(db)
    return await repo.get_analytics(provider=provider, user_id=user["user_id"])


@router.get("/compare", summary="Compare providers", description="Compare evaluation metrics between OpenAI and Ollama providers.")
async def compare_providers(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    repo = EvaluationRepository(db)
    return await repo.compare_providers(user_id=user["user_id"])
