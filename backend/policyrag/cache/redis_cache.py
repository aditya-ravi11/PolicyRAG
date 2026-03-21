import hashlib
import json
import logging
from typing import Optional

import redis.asyncio as aioredis

from policyrag.config import settings

logger = logging.getLogger(__name__)


class QueryCache:
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        try:
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await self._redis.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self._redis = None

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()

    def _make_key(self, query: str, doc_ids: list[str], provider: str, model: str) -> str:
        raw = json.dumps({"q": query, "docs": sorted(doc_ids), "p": provider, "m": model}, sort_keys=True)
        return f"policyrag:query:{hashlib.sha256(raw.encode()).hexdigest()}"

    async def get(self, query: str, doc_ids: list[str], provider: str, model: str) -> Optional[dict]:
        if not self._redis:
            return None
        try:
            key = self._make_key(query, doc_ids, provider, model)
            data = await self._redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None

    async def set(self, query: str, doc_ids: list[str], provider: str, model: str, response: dict) -> None:
        if not self._redis:
            return
        try:
            key = self._make_key(query, doc_ids, provider, model)
            await self._redis.set(key, json.dumps(response), ex=settings.CACHE_TTL_SECONDS)
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    async def invalidate_for_document(self, doc_id: str) -> None:
        """Invalidate all cached queries (simple approach: flush all query keys)."""
        if not self._redis:
            return
        try:
            async for key in self._redis.scan_iter("policyrag:query:*"):
                await self._redis.delete(key)
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
