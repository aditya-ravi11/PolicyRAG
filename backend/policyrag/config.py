from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://policyrag:policyrag@localhost:5432/policyrag"
    REDIS_URL: str = "redis://localhost:6379/0"
    CHROMA_HOST: Optional[str] = None
    CHROMA_PORT: int = 8000
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    DEFAULT_LLM_PROVIDER: str = "groq"
    DEFAULT_LLM_MODEL: str = "llama-3.3-70b-versatile"
    EDGAR_USER_AGENT: str = "PolicyRAG admin@example.com"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    NLI_MODEL: str = "cross-encoder/nli-deberta-v3-base"
    CHROMA_COLLECTION: str = "policyrag_chunks"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 200
    DEFAULT_TOP_K: int = 10
    CACHE_TTL_SECONDS: int = 3600

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
