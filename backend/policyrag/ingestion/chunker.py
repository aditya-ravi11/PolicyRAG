from dataclasses import dataclass
from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from policyrag.config import settings


@dataclass
class Chunk:
    text: str
    metadata: dict


def chunk_text(
    text: str,
    doc_id: str,
    section: str = "Unknown",
    page_num: Optional[int] = None,
    company: Optional[str] = None,
    filing_type: Optional[str] = None,
    filing_date: Optional[str] = None,
    user_id: Optional[str] = None,
) -> list[Chunk]:
    """Split text into chunks with metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    texts = splitter.split_text(text)
    chunks = []
    for idx, t in enumerate(texts):
        metadata = {
            "doc_id": doc_id,
            "section": section,
            "chunk_idx": idx,
        }
        if page_num is not None:
            metadata["page_num"] = page_num
        if company:
            metadata["company"] = company
        if filing_type:
            metadata["filing_type"] = filing_type
        if filing_date:
            metadata["filing_date"] = filing_date
        if user_id:
            metadata["user_id"] = user_id
        chunks.append(Chunk(text=t, metadata=metadata))
    return chunks
