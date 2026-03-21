import numpy as np

from policyrag.core.retriever import RetrievedChunk
from policyrag.ingestion.embedder import embed_query, embed_texts


async def evaluate_context_relevance(
    query: str,
    chunks: list[RetrievedChunk],
) -> float:
    """Average cosine similarity between query and each retrieved chunk."""
    if not chunks:
        return 0.0

    query_emb = await embed_query(query)
    chunk_texts = [c.text for c in chunks]
    chunk_embs = await embed_texts(chunk_texts)

    query_vec = np.array(query_emb)
    similarities = []
    for emb in chunk_embs:
        chunk_vec = np.array(emb)
        cos_sim = np.dot(query_vec, chunk_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec) + 1e-8)
        similarities.append(float(cos_sim))

    return sum(similarities) / len(similarities)
