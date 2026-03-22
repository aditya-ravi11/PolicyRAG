import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from policyrag.auth.jwt_verifier import get_current_user
from policyrag.core.query_expander import expand_query
from policyrag.ingestion.embedder import embed_query
from policyrag.ingestion.pipeline import get_collection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/retrieval", summary="Debug retrieval pipeline", description="Shows raw retrieval results at each stage for a given query.")
async def debug_retrieval(
    q: str = Query(..., description="Query to test"),
    top_k: int = Query(20, description="Number of results"),
    user: dict = Depends(get_current_user),
):
    """Debug endpoint showing what the retrieval pipeline returns at each stage."""
    collection = get_collection()
    total_chunks = collection.count()

    # Step 1: Expand query
    expanded = expand_query(q)

    # Step 2: Embed expanded query
    embedding = await embed_query(expanded)

    # Step 3: Raw ChromaDB results (no metadata filter)
    raw_results = collection.query(
        query_embeddings=[embedding],
        n_results=min(top_k, 50),
        include=["documents", "metadatas", "distances"],
    )

    raw_items = []
    if raw_results["ids"] and raw_results["ids"][0]:
        for i, cid in enumerate(raw_results["ids"][0]):
            score = 1.0 - raw_results["distances"][0][i]
            doc = raw_results["documents"][0][i]
            meta = raw_results["metadatas"][0][i]
            raw_items.append({
                "chunk_id": cid,
                "text_preview": doc[:150],
                "score": round(score, 4),
                "section": meta.get("section"),
                "page_num": meta.get("page_num"),
                "company": meta.get("company"),
                "has_revenue_keyword": "revenue" in doc.lower() or "net sales" in doc.lower(),
            })

    return {
        "query": q,
        "expanded_query": expanded,
        "embedding_preview": [round(x, 4) for x in embedding[:10]],
        "total_chunks_in_store": total_chunks,
        "raw_results": raw_items,
    }
