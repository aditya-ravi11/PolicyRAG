import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from policyrag.api.deps import _cache
from policyrag.api.routes import documents, evaluation, models, query

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
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
        logger.warning(f"Failed to create database tables: {e}")

    await _cache.connect()

    # Pre-warm models
    try:
        from policyrag.ingestion.embedder import _get_model
        _get_model()
        logger.info("Embedding model loaded")
    except Exception as e:
        logger.warning(f"Failed to pre-load embedding model: {e}")

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router)
app.include_router(documents.router)
app.include_router(evaluation.router)
app.include_router(models.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
