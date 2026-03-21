import asyncio
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from policyrag.config import settings


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(settings.EMBEDDING_MODEL)


def _embed_sync(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch embed texts using sentence-transformers in a thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _embed_sync, texts)


async def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    results = await embed_texts([query])
    return results[0]
