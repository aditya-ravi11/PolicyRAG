import logging
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from policyrag.api.deps import _cache
from policyrag.api.routes import debug, documents, evaluation, models, query
from policyrag.config import settings
from policyrag.logging_config import setup_logging

setup_logging(json_format=os.getenv("LOG_FORMAT", "json") == "json")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting PolicyRAG API")

    # Create DB tables if they don't exist
    try:
        from policyrag.db.models import Base
        from policyrag.db.session import engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ready")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}", exc_info=True)

    await _cache.connect()

    # Pre-warm models
    try:
        from policyrag.ingestion.embedder import _get_model
        _get_model()
        logger.info("Embedding model loaded")
    except Exception as e:
        logger.error(f"Failed to pre-load embedding model: {e}", exc_info=True)

    yield

    # Shutdown
    await _cache.close()
    logger.info("PolicyRAG API shutdown")


app = FastAPI(
    title="PolicyRAG API",
    description="RAG system for SEC financial filing QA with hallucination scoring",
    version="0.1.0",
    lifespan=lifespan,
)


# Security headers middleware — runs BEFORE rate limiter
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


# Rate limiting
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "30"))  # requests per window (IP-based)
USER_RATE_LIMIT_WINDOW = 3600  # 1 hour
USER_RATE_LIMIT_MAX = int(os.getenv("USER_RATE_LIMIT_MAX", "60"))  # queries per hour per user
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
_user_rate_limit_store: dict[str, list[float]] = defaultdict(list)


def _extract_user_id_from_jwt(request: Request) -> str | None:
    """Try to extract user_id from JWT in Authorization header (lightweight, no full validation)."""
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    try:
        import jwt
        # Decode without verification just to extract sub for rate limiting
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload.get("sub")
    except Exception:
        return None


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Only rate-limit POST query endpoints (not GET eval polling)
    if request.url.path.startswith("/api/v1/query") and request.method == "POST":
        now = time.time()
        client_ip = request.client.host if request.client else "unknown"

        # IP-based rate limiting
        _rate_limit_store[client_ip] = [
            t for t in _rate_limit_store[client_ip] if now - t < RATE_LIMIT_WINDOW
        ]
        if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
            retry_after = int(RATE_LIMIT_WINDOW - (now - _rate_limit_store[client_ip][0]))
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={"Retry-After": str(max(retry_after, 1))},
            )
        _rate_limit_store[client_ip].append(now)

        # Per-user rate limiting (if JWT present)
        user_id = _extract_user_id_from_jwt(request)
        if user_id:
            key = f"user:{user_id}"
            _user_rate_limit_store[key] = [
                t for t in _user_rate_limit_store[key] if now - t < USER_RATE_LIMIT_WINDOW
            ]
            if len(_user_rate_limit_store[key]) >= USER_RATE_LIMIT_MAX:
                retry_after = int(USER_RATE_LIMIT_WINDOW - (now - _user_rate_limit_store[key][0]))
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Per-user rate limit exceeded. Please try again later."},
                    headers={"Retry-After": str(max(retry_after, 1))},
                )
            _user_rate_limit_store[key].append(now)

    return await call_next(request)


cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router)
app.include_router(documents.router)
app.include_router(evaluation.router)
app.include_router(models.router)
app.include_router(debug.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
