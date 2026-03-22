import asyncio
import logging
import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from sentence_transformers import CrossEncoder

from policyrag.config import settings
from policyrag.core.query_expander import expand_query
from policyrag.ingestion.embedder import embed_query
from policyrag.ingestion.pipeline import get_collection

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float
    metadata: dict


@lru_cache(maxsize=1)
def _get_reranker() -> CrossEncoder:
    return CrossEncoder(settings.RERANKER_MODEL)


def _rerank_sync(query: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    reranker = _get_reranker()
    pairs = [(query, c.text) for c in chunks]
    scores = reranker.predict(pairs)
    for chunk, score in zip(chunks, scores):
        # Normalize raw cross-encoder logits to 0-1 via sigmoid
        chunk.score = 1.0 / (1.0 + math.exp(-float(score)))
    chunks.sort(key=lambda c: c.score, reverse=True)
    return chunks[:top_k]


async def retrieve(
    query: str,
    top_k: int = 10,
    rerank: bool = True,
    company_filter: Optional[str] = None,
    section_filter: Optional[str] = None,
    filing_type_filter: Optional[str] = None,
    document_ids: Optional[list[str]] = None,
    user_id: Optional[str] = None,
) -> list[RetrievedChunk]:
    """Retrieve relevant chunks from ChromaDB with optional re-ranking."""
    # Expand query with financial synonyms for better recall
    expanded_query = expand_query(query)

    # Embed the expanded query for semantic search
    query_embedding = await embed_query(expanded_query)

    # Build metadata filter — ChromaDB requires $and for multiple conditions
    conditions = []
    if user_id:
        conditions.append({"user_id": user_id})
    if company_filter:
        conditions.append({"company": company_filter})
    if section_filter:
        conditions.append({"section": section_filter})
    if filing_type_filter:
        conditions.append({"filing_type": filing_type_filter})
    if document_ids:
        conditions.append({"doc_id": {"$in": document_ids}})

    where = {}
    if len(conditions) == 1:
        where = conditions[0]
    elif len(conditions) > 1:
        where = {"$and": conditions}

    collection = get_collection()
    n_results = top_k * 3 if rerank else top_k

    query_kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": min(n_results, 50),
    }
    if where:
        query_kwargs["where"] = where

    results = collection.query(**query_kwargs)

    chunks = []
    if results["ids"] and results["ids"][0]:
        for i, chunk_id in enumerate(results["ids"][0]):
            chunks.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    text=results["documents"][0][i],
                    score=1.0 - (results["distances"][0][i] if results["distances"] else 0),
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                )
            )

    # Filter by embedding similarity BEFORE reranking
    min_score = settings.MIN_RETRIEVAL_SCORE
    chunks = [c for c in chunks if c.score >= min_score]

    if rerank and chunks:
        # Rerank using the ORIGINAL query (not expanded) for precision.
        # Cross-encoder scores are used for relative ordering only — the
        # absolute threshold was already applied to embedding scores above.
        loop = asyncio.get_event_loop()
        chunks = await loop.run_in_executor(None, _rerank_sync, query, chunks, top_k)
    else:
        chunks = chunks[:top_k]

    return chunks
