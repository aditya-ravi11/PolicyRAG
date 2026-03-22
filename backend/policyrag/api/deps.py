from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from policyrag.auth.jwt_verifier import get_current_user
from policyrag.cache.redis_cache import QueryCache
from policyrag.core.rag_pipeline import RAGPipeline
from policyrag.db.session import get_session
from policyrag.evaluation.engine import EvaluationEngine
from policyrag.llm.factory import LLMFactory

# Singletons
_cache = QueryCache()
_eval_engine = EvaluationEngine()
_rag_pipeline = RAGPipeline(eval_engine=_eval_engine)


def get_cache() -> QueryCache:
    return _cache


def get_rag_pipeline() -> RAGPipeline:
    return _rag_pipeline


def get_eval_engine() -> EvaluationEngine:
    return _eval_engine


def get_llm_factory() -> type[LLMFactory]:
    return LLMFactory


async def get_db(session: AsyncSession = Depends(get_session)):
    return session
