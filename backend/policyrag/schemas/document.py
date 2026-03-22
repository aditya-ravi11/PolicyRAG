from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentUpload(BaseModel):
    company: Optional[str] = None
    filing_type: Optional[str] = None
    filing_date: Optional[date] = None
    ticker: Optional[str] = None


VALID_FILING_TYPES = {"10-K", "10-Q", "8-K", "20-F", "6-K", "S-1", "DEF 14A"}


class EdgarRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10, pattern=r"^[A-Za-z]{1,5}$")
    filing_type: str = Field(default="10-K")
    date_after: Optional[str] = None
    date_before: Optional[str] = None

    @classmethod
    def model_validate(cls, *args, **kwargs):
        obj = super().model_validate(*args, **kwargs)
        if obj.filing_type not in VALID_FILING_TYPES:
            raise ValueError(f"Invalid filing_type '{obj.filing_type}'. Must be one of: {', '.join(sorted(VALID_FILING_TYPES))}")
        return obj


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
