import logging
import time
import uuid
from typing import Optional

from policyrag.core.citation_extractor import extract_citations
from policyrag.core.context_builder import build_context
from policyrag.core.response_assembler import assemble_response
from policyrag.core.retriever import retrieve
from policyrag.evaluation.engine import EvaluationEngine
from policyrag.llm.base import BaseLLMProvider
from policyrag.llm.factory import LLMFactory
from policyrag.llm.prompts import VANILLA_RAG_PROMPT
from policyrag.schemas.query import CompareResponse, QueryRequest, QueryResponse, VanillaResponse

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self, eval_engine: Optional[EvaluationEngine] = None):
        self.eval_engine = eval_engine

    async def query(self, request: QueryRequest) -> QueryResponse:
        query_id = str(uuid.uuid4())
        provider_name = request.provider or LLMFactory.get_active()[0]
        model_name = request.model or LLMFactory.get_active()[1]

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
            )
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            chunks = []
        latency_retrieval = (time.time() - t0) * 1000

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

        # Extract citations
        extraction = extract_citations(llm_response.content, context_result.source_map)

        # Evaluate (async, best effort)
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
                logger.error(f"Evaluation failed: {e}")

        return assemble_response(
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

    async def compare(self, request: QueryRequest) -> CompareResponse:
        """Run vanilla RAG and PolicyRAG side-by-side with shared retrieval."""
        query_id = str(uuid.uuid4())
        provider_name = request.provider or LLMFactory.get_active()[0]
        model_name = request.model or LLMFactory.get_active()[1]

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
            )
        except Exception as e:
            logger.error(f"Retrieval failed in compare: {e}")
            chunks = []
        latency_retrieval = (time.time() - t0) * 1000

        if not chunks:
            raise ValueError(
                "No documents found. Please upload SEC filings or fetch from EDGAR before querying."
            )

        # Shared context
        context_result = build_context(chunks)

        # 1) Vanilla pipeline — simple prompt, no citations, no guardrails
        t_vanilla = time.time()
        vanilla_prompt = VANILLA_RAG_PROMPT.format(
            context=context_result.formatted_text,
            query=request.query,
        )
        vanilla_llm_response = await llm.generate(vanilla_prompt)
        latency_vanilla = (time.time() - t_vanilla) * 1000

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
                logger.error(f"Evaluation failed in compare: {e}")

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
