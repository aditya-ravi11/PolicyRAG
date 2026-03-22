import logging
import time
import uuid
from typing import Any, Optional

from policyrag.core.citation_extractor import extract_citations
from policyrag.core.context_builder import build_context
from policyrag.core.response_assembler import assemble_response
from policyrag.core.retriever import retrieve
from policyrag.evaluation.engine import EvaluationEngine
from policyrag.llm.base import BaseLLMProvider
from policyrag.llm.factory import LLMFactory
from policyrag.llm.prompts import VANILLA_RAG_SYSTEM_PROMPT
from policyrag.schemas.query import (
    CompareResponse, EvaluationScores, QueryRequest, QueryResponse, VanillaResponse,
)

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self, eval_engine: Optional[EvaluationEngine] = None):
        self.eval_engine = eval_engine

    async def query(self, request: QueryRequest, user_id: Optional[str] = None) -> tuple[QueryResponse, dict]:
        """Run retrieve → generate → citations.  Returns (response, eval_context).

        Evaluation is NOT run here — the caller fires it as a background task.
        """
        query_id = str(uuid.uuid4())
        provider_name = request.provider or LLMFactory.get_active()[0]
        model_name = request.model or LLMFactory.get_active()[1]
        log_extra = {"query_id": query_id, "provider": provider_name, "model": model_name}

        # Create LLM provider
        llm = LLMFactory.create(provider=provider_name, model=model_name)

        # Retrieve
        t0 = time.time()
        try:
            chunks = await retrieve(
                query=request.query,
                top_k=request.retrieval_config.top_k,
                rerank=request.retrieval_config.rerank,
                company_filter=request.retrieval_config.company_filter,
                section_filter=request.retrieval_config.section_filter,
                filing_type_filter=request.retrieval_config.filing_type_filter,
                document_ids=request.document_ids or None,
                user_id=user_id,
            )
        except Exception as e:
            logger.error(f"Retrieval failed: {e}", extra={**log_extra, "stage": "retrieval"})
            chunks = []
        latency_retrieval = (time.time() - t0) * 1000
        logger.info(
            f"Retrieval completed: {len(chunks)} chunks in {latency_retrieval:.1f}ms",
            extra={**log_extra, "stage": "retrieval", "latency_ms": round(latency_retrieval, 1), "num_chunks": len(chunks)},
        )

        if not chunks:
            raise ValueError(
                "No documents found. Please upload SEC filings or fetch from EDGAR before querying."
            )

        # Build context
        context_result = build_context(chunks)

        # Generate
        t1 = time.time()
        llm_response = await llm.generate_with_context(
            query=request.query,
            context=context_result.formatted_text,
        )
        latency_generation = (time.time() - t1) * 1000
        logger.info(
            f"Generation completed in {latency_generation:.1f}ms",
            extra={**log_extra, "stage": "generation", "latency_ms": round(latency_generation, 1)},
        )

        # Extract citations
        extraction = extract_citations(llm_response.content, context_result.source_map)

        total_ms = latency_retrieval + latency_generation
        logger.info(
            f"Pipeline completed in {total_ms:.1f}ms (evaluation deferred)",
            extra={**log_extra, "stage": "pipeline_total", "latency_ms": round(total_ms, 1)},
        )

        response = assemble_response(
            query_id=query_id,
            query=request.query,
            answer=llm_response.content,
            extraction=extraction,
            evaluation=None,
            provider=provider_name,
            model=model_name,
            num_chunks=len(chunks),
            latency_retrieval_ms=latency_retrieval,
            latency_generation_ms=latency_generation,
            latency_evaluation_ms=0,
        )
        response.evaluation_status = "pending"

        # Context needed by background evaluation
        eval_context = {
            "query_id": query_id,
            "query": request.query,
            "answer": llm_response.content,
            "chunks": chunks,
            "source_map": context_result.source_map,
            "citations": extraction.citations,
            "llm": llm,
            "provider": provider_name,
            "model": model_name,
            "num_chunks": len(chunks),
            "latency_retrieval_ms": latency_retrieval,
            "latency_generation_ms": latency_generation,
        }

        return response, eval_context

    async def run_background_evaluation(
        self,
        eval_context: dict,
        async_session_factory: Any,
        cache: Any,
        cache_key_params: dict,
        user_id: Optional[str] = None,
    ) -> None:
        """Run evaluation in background, persist to DB, and update cache."""
        if not self.eval_engine:
            return

        query_id = eval_context["query_id"]
        log_extra = {"query_id": query_id, "stage": "background_evaluation"}

        try:
            t2 = time.time()
            evaluation = await self.eval_engine.evaluate(
                query=eval_context["query"],
                answer=eval_context["answer"],
                context_chunks=eval_context["chunks"],
                source_map=eval_context["source_map"],
                citations=eval_context["citations"],
                llm=eval_context["llm"],
            )
            latency_eval = (time.time() - t2) * 1000
            logger.info(
                f"Background evaluation completed in {latency_eval:.1f}ms",
                extra={
                    **log_extra,
                    "latency_ms": round(latency_eval, 1),
                    "score": evaluation.overall_trust_score if evaluation else None,
                },
            )

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

            # Persist to DB using its own session
            if evaluation and evaluation.overall_trust_score is not None:
                try:
                    from policyrag.db.repositories.evaluation_repo import EvaluationRepository
                    async with async_session_factory() as session:
                        repo = EvaluationRepository(session)
                        create_kwargs = dict(
                            query_id=uuid.UUID(query_id),
                            query_text=eval_context["query"],
                            answer_text=eval_context["answer"],
                            provider=eval_context["provider"],
                            model=eval_context["model"],
                            faithfulness_score=evaluation.faithfulness_score,
                            hallucination_score=evaluation.hallucination_score,
                            citation_precision=evaluation.citation_precision,
                            citation_recall=evaluation.citation_recall,
                            context_relevance=evaluation.context_relevance,
                            completeness_score=evaluation.completeness_score,
                            overall_trust_score=evaluation.overall_trust_score,
                            num_chunks_retrieved=eval_context["num_chunks"],
                            latency_retrieval_ms=eval_context["latency_retrieval_ms"],
                            latency_generation_ms=eval_context["latency_generation_ms"],
                            latency_evaluation_ms=latency_eval,
                        )
                        if user_id:
                            create_kwargs["user_id"] = user_id
                        await repo.create(**create_kwargs)
                except Exception as e:
                    logger.error(f"Failed to persist background evaluation: {e}", extra=log_extra)

            # Update cache with evaluation scores
            try:
                cached_data = await cache.get(**cache_key_params)
                if cached_data:
                    cached_data["evaluation"] = eval_scores.model_dump()
                    cached_data["evaluation_status"] = "completed"
                    cached_data["metadata"]["latency_evaluation_ms"] = round(latency_eval, 1)
                    await cache.set(**cache_key_params, response=cached_data)
            except Exception as e:
                logger.warning(f"Failed to update cache with evaluation: {e}", extra=log_extra)

        except Exception as e:
            logger.error(f"Background evaluation failed: {e}", extra=log_extra)

    async def compare(self, request: QueryRequest, user_id: Optional[str] = None) -> CompareResponse:
        """Run vanilla RAG and PolicyRAG side-by-side with shared retrieval."""
        query_id = str(uuid.uuid4())
        provider_name = request.provider or LLMFactory.get_active()[0]
        model_name = request.model or LLMFactory.get_active()[1]
        log_extra = {"query_id": query_id, "provider": provider_name, "model": model_name}

        llm = LLMFactory.create(provider=provider_name, model=model_name)

        # Shared retrieval
        t0 = time.time()
        try:
            chunks = await retrieve(
                query=request.query,
                top_k=request.retrieval_config.top_k,
                rerank=request.retrieval_config.rerank,
                company_filter=request.retrieval_config.company_filter,
                section_filter=request.retrieval_config.section_filter,
                filing_type_filter=request.retrieval_config.filing_type_filter,
                document_ids=request.document_ids or None,
                user_id=user_id,
            )
        except Exception as e:
            logger.error(f"Retrieval failed in compare: {e}", extra={**log_extra, "stage": "retrieval"})
            chunks = []
        latency_retrieval = (time.time() - t0) * 1000

        if not chunks:
            raise ValueError(
                "No documents found. Please upload SEC filings or fetch from EDGAR before querying."
            )

        # Shared context
        context_result = build_context(chunks)

        # 1) Vanilla pipeline — simple system prompt, no citations, no guardrails
        t_vanilla = time.time()
        vanilla_llm_response = await llm.generate_with_context(
            query=request.query,
            context=context_result.formatted_text,
            system_prompt=VANILLA_RAG_SYSTEM_PROMPT,
        )
        latency_vanilla = (time.time() - t_vanilla) * 1000
        logger.info(
            f"Vanilla generation completed in {latency_vanilla:.1f}ms",
            extra={**log_extra, "stage": "vanilla_generation", "latency_ms": round(latency_vanilla, 1)},
        )

        vanilla = VanillaResponse(
            answer=vanilla_llm_response.content,
            latency_ms=latency_vanilla,
            provider=provider_name,
            model=model_name,
        )

        # 2) PolicyRAG pipeline — full citations + evaluation
        t1 = time.time()
        llm_response = await llm.generate_with_context(
            query=request.query,
            context=context_result.formatted_text,
        )
        latency_generation = (time.time() - t1) * 1000

        extraction = extract_citations(llm_response.content, context_result.source_map)

        evaluation = None
        latency_eval = 0.0
        if self.eval_engine:
            try:
                t2 = time.time()
                evaluation = await self.eval_engine.evaluate(
                    query=request.query,
                    answer=llm_response.content,
                    context_chunks=chunks,
                    source_map=context_result.source_map,
                    citations=extraction.citations,
                    llm=llm,
                )
                latency_eval = (time.time() - t2) * 1000
            except Exception as e:
                logger.error(f"Evaluation failed in compare: {e}", extra={**log_extra, "stage": "evaluation"})

        policyrag_response = assemble_response(
            query_id=query_id,
            query=request.query,
            answer=llm_response.content,
            extraction=extraction,
            evaluation=evaluation,
            provider=provider_name,
            model=model_name,
            num_chunks=len(chunks),
            latency_retrieval_ms=latency_retrieval,
            latency_generation_ms=latency_generation,
            latency_evaluation_ms=latency_eval,
        )

        return CompareResponse(
            query=request.query,
            vanilla=vanilla,
            policyrag=policyrag_response,
        )
