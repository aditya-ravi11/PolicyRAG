import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from policyrag.api.deps import get_cache, get_db, get_rag_pipeline
from policyrag.cache.redis_cache import QueryCache
from policyrag.core.rag_pipeline import RAGPipeline
from policyrag.db.repositories.evaluation_repo import EvaluationRepository
from policyrag.llm.factory import LLMFactory
from policyrag.schemas.query import CompareResponse, QueryRequest, QueryResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/query", tags=["query"])


@router.post("", response_model=QueryResponse, summary="Query documents", description="Run a RAG query against ingested SEC filings. Returns an answer with citations and evaluation scores.")
async def query_documents(
    request: QueryRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
    cache: QueryCache = Depends(get_cache),
    db: AsyncSession = Depends(get_db),
):
    """Execute a RAG query with citation extraction and trust evaluation."""
    provider = request.provider or LLMFactory.get_active()[0]
    model = request.model or LLMFactory.get_active()[1]

    # Check cache
    if not request.no_cache:
        cached = await cache.get(request.query, request.document_ids, provider, model)
        if cached:
            return QueryResponse(**cached)

    try:
        response = await pipeline.query(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Persist evaluation to DB
    if response.evaluation and response.evaluation.overall_trust_score is not None:
        try:
            repo = EvaluationRepository(db)
            await repo.create(
                query_id=uuid.UUID(response.query_id),
                query_text=response.query,
                answer_text=response.answer,
                provider=response.metadata.provider,
                model=response.metadata.model,
                faithfulness_score=response.evaluation.faithfulness,
                hallucination_score=response.evaluation.hallucination_score,
                citation_precision=response.evaluation.citation_precision,
                citation_recall=response.evaluation.citation_recall,
                context_relevance=response.evaluation.context_relevance,
                completeness_score=response.evaluation.completeness,
                overall_trust_score=response.evaluation.overall_trust_score,
                num_chunks_retrieved=response.metadata.num_chunks_retrieved,
                latency_retrieval_ms=response.metadata.latency_retrieval_ms,
                latency_generation_ms=response.metadata.latency_generation_ms,
                latency_evaluation_ms=response.metadata.latency_evaluation_ms,
            )
        except Exception as e:
            logger.error(f"Failed to persist evaluation: {e}")

    # Cache result
    await cache.set(request.query, request.document_ids, provider, model, response.model_dump())

    return response


@router.post("/compare", response_model=CompareResponse, summary="Compare vanilla vs PolicyRAG", description="Run both vanilla RAG and PolicyRAG on the same query with shared retrieval.")
async def compare_query(
    request: QueryRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
):
    """Execute a side-by-side comparison of vanilla RAG vs PolicyRAG."""
    try:
        response = await pipeline.compare(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return response


@router.post("/stream", summary="Stream query response", description="Run a RAG query with server-sent events for real-time streaming.")
async def query_stream(
    request: QueryRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
):
    """Stream a RAG query response via server-sent events."""
    async def event_generator():
        yield {"event": "status", "data": json.dumps({"status": "retrieving"})}
        try:
            response = await pipeline.query(request)
            yield {"event": "answer", "data": response.model_dump_json()}
            yield {"event": "done", "data": ""}
        except ValueError as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
        except ConnectionError as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())
