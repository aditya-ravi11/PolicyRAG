import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from policyrag.db.models import EvaluationHistory


class EvaluationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> EvaluationHistory:
        record = EvaluationHistory(**kwargs)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get_by_query_id(self, query_id: uuid.UUID) -> Optional[EvaluationHistory]:
        result = await self.session.execute(
            select(EvaluationHistory).where(EvaluationHistory.query_id == query_id)
        )
        return result.scalar_one_or_none()

    async def list_history(self, limit: int = 50, offset: int = 0, provider: Optional[str] = None) -> list[EvaluationHistory]:
        stmt = select(EvaluationHistory).order_by(EvaluationHistory.created_at.desc()).limit(limit).offset(offset)
        if provider:
            stmt = stmt.where(EvaluationHistory.provider == provider)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_analytics(self, provider: Optional[str] = None) -> dict:
        stmt = select(
            func.count(EvaluationHistory.id).label("total_queries"),
            func.avg(EvaluationHistory.faithfulness_score).label("avg_faithfulness"),
            func.avg(EvaluationHistory.hallucination_score).label("avg_hallucination"),
            func.avg(EvaluationHistory.citation_precision).label("avg_citation_precision"),
            func.avg(EvaluationHistory.citation_recall).label("avg_citation_recall"),
            func.avg(EvaluationHistory.context_relevance).label("avg_context_relevance"),
            func.avg(EvaluationHistory.overall_trust_score).label("avg_trust_score"),
            func.avg(EvaluationHistory.completeness_score).label("avg_completeness"),
        )
        if provider:
            stmt = stmt.where(EvaluationHistory.provider == provider)
        result = await self.session.execute(stmt)
        row = result.one()
        return {
            "total_queries": row.total_queries or 0,
            "avg_faithfulness": round(float(row.avg_faithfulness or 0), 3),
            "avg_hallucination": round(float(row.avg_hallucination or 0), 3),
            "avg_citation_precision": round(float(row.avg_citation_precision or 0), 3),
            "avg_citation_recall": round(float(row.avg_citation_recall or 0), 3),
            "avg_context_relevance": round(float(row.avg_context_relevance or 0), 3),
            "avg_trust_score": round(float(row.avg_trust_score or 0), 3),
            "avg_completeness": round(float(row.avg_completeness or 0), 3),
        }

    async def compare_providers(self) -> dict:
        providers = {}
        for provider in ["openai", "ollama"]:
            providers[provider] = await self.get_analytics(provider=provider)
        return providers
