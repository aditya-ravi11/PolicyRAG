import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    company: Mapped[str | None] = mapped_column(String(300))
    filing_type: Mapped[str | None] = mapped_column(String(50))
    filing_date: Mapped[date | None] = mapped_column(Date)
    cik: Mapped[str | None] = mapped_column(String(20))
    ticker: Mapped[str | None] = mapped_column(String(10))
    source_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PROCESSING")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    file_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class EvaluationHistory(Base):
    __tablename__ = "evaluation_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    query_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    faithfulness_score: Mapped[float | None] = mapped_column(Float)
    citation_precision: Mapped[float | None] = mapped_column(Float)
    citation_recall: Mapped[float | None] = mapped_column(Float)
    context_relevance: Mapped[float | None] = mapped_column(Float)
    hallucination_score: Mapped[float | None] = mapped_column(Float)
    completeness_score: Mapped[float | None] = mapped_column(Float)
    overall_trust_score: Mapped[float | None] = mapped_column(Float)
    num_claims: Mapped[int | None] = mapped_column(Integer)
    num_faithful_claims: Mapped[int | None] = mapped_column(Integer)
    num_chunks_retrieved: Mapped[int | None] = mapped_column(Integer)
    latency_retrieval_ms: Mapped[float | None] = mapped_column(Float)
    latency_generation_ms: Mapped[float | None] = mapped_column(Float)
    latency_evaluation_ms: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class QueryCitation(Base):
    __tablename__ = "query_citations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    citation_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_id: Mapped[str] = mapped_column(String(200), nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    section: Mapped[str | None] = mapped_column(String(100))
    page_num: Mapped[int | None] = mapped_column(Integer)
    relevance_score: Mapped[float | None] = mapped_column(Float)
    is_faithful: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
