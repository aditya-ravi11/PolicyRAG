from typing import Optional

from pydantic import BaseModel


class SourceChunk(BaseModel):
    chunk_id: str
    text: str
    document_id: Optional[str] = None
    section: Optional[str] = None
    page_num: Optional[int] = None
    relevance_score: float = 0.0
    company: Optional[str] = None
    filing_type: Optional[str] = None


class Citation(BaseModel):
    index: int
    chunk: SourceChunk
    is_faithful: Optional[bool] = None


class CitedAnswer(BaseModel):
    answer: str
    citations: list[Citation]
    source_chunks: list[SourceChunk]
    citation_coverage: float = 0.0
