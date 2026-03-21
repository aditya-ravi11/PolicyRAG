from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentUpload(BaseModel):
    company: Optional[str] = None
    filing_type: Optional[str] = None
    filing_date: Optional[date] = None
    ticker: Optional[str] = None


class EdgarRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    filing_type: str = Field(default="10-K")
    date_after: Optional[str] = None
    date_before: Optional[str] = None


class DocumentResponse(BaseModel):
    id: str
    filename: str
    company: Optional[str] = None
    filing_type: Optional[str] = None
    filing_date: Optional[date] = None
    ticker: Optional[str] = None
    status: str
    chunk_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}
