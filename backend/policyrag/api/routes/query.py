import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from policyrag.api.deps import get_cache, get_db, get_rag_pipeline
from policyrag.auth.jwt_verifier import get_current_user
from policyrag.cache.redis_cache import QueryCache
from policyrag.core.rag_pipeline import RAGPipeline
from policyrag.core.sanitizer import PromptInjectionError, sanitize_query
from policyrag.db.repositories.evaluation_repo import EvaluationRepository
from policyrag.db.session import async_session_factory
from policyrag.llm.factory import LLMFactory
from policyrag.schemas.query import (
    CompareResponse, EvaluationPollResponse, EvaluationScores,
    QueryRequest, QueryResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/query", tags=["query"])


@router.post("", response_model=QueryResponse, summary="Query documents", description="Run a RAG query against ingested SEC filings. Returns an answer with citations and evaluation scores.")
async def query_documents(
    request: QueryRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
    cache: QueryCache = Depends(get_cache),
    user: dict = Depends(get_current_user),
):
    """Execute a RAG query with citation extraction and trust evaluation."""
    try:
        request.query = sanitize_query(request.query)
    except PromptInjectionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user_id = user["user_id"]
    provider = request.provider or LLMFactory.get_active()[0]
    model = request.model or LLMFactory.get_active()[1]
    rc = request.retrieval_config

    cache_key_params = dict(
        query=request.query, doc_ids=request.document_ids, provider=provider, model=model,
        top_k=rc.top_k, rerank=rc.rerank,
        company_filter=rc.company_filter,
        section_filter=rc.section_filter,
        filing_type_filter=rc.filing_type_filter,
    )

    # Check cache — if cached response has evaluation, return as completed
    if not request.no_cache:
        cached = await cache.get(**cache_key_params)
        if cached:
            return QueryResponse(**cached)

    try:
        response, eval_context = await pipeline.query(request, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Cache immediate response (evaluation_status="pending")
    await cache.set(**cache_key_params, response=response.model_dump())

    # Fire background evaluation
    asyncio.create_task(
        pipeline.run_background_evaluation(
            eval_context=eval_context,
            async_session_factory=async_session_factory,
            cache=cache,
            cache_key_params=cache_key_params,
            user_id=user_id,
        )
    )

    return response


@router.get("/{query_id}/evaluation", response_model=EvaluationPollResponse, summary="Poll evaluation status")
async def poll_evaluation(
    query_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Poll for evaluation results of a previously submitted query."""
    try:
        uid = uuid.UUID(query_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid query_id")

    repo = EvaluationRepository(db)
    record = await repo.get_by_query_id(uid, user_id=user["user_id"])

    if not record:
        return EvaluationPollResponse(status="pending")

    return EvaluationPollResponse(
        status="completed",
        evaluation=EvaluationScores(
            faithfulness=record.faithfulness_score,
            hallucination_score=record.hallucination_score,
            citation_precision=record.citation_precision,
            citation_recall=record.citation_recall,
            context_relevance=record.context_relevance,
            completeness=record.completeness_score,
            overall_trust_score=record.overall_trust_score,
        ),
        latency_evaluation_ms=record.latency_evaluation_ms,
    )


@router.post("/compare", response_model=CompareResponse, summary="Compare vanilla vs PolicyRAG", description="Run both vanilla RAG and PolicyRAG on the same query with shared retrieval.")
async def compare_query(
    request: QueryRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
    user: dict = Depends(get_current_user),
):
    """Execute a side-by-side comparison of vanilla RAG vs PolicyRAG."""
    try:
        request.query = sanitize_query(request.query)
    except PromptInjectionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        response = await pipeline.compare(request, user_id=user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return response


@router.post("/stream", summary="Stream query response", description="Run a RAG query with server-sent events for real-time streaming.")
async def query_stream(
    request: QueryRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
    user: dict = Depends(get_current_user),
):
    """Stream a RAG query response via server-sent events."""
    user_id = user["user_id"]

    async def event_generator():
        yield {"event": "status", "data": json.dumps({"status": "retrieving"})}
        try:
            response, _eval_context = await pipeline.query(request, user_id=user_id)
            yield {"event": "answer", "data": response.model_dump_json()}
            yield {"event": "done", "data": ""}
        except ValueError as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
        except ConnectionError as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())
