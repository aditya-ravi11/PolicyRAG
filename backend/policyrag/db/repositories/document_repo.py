import uuid
from datetime import date
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from policyrag.db.models import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        filename: str,
        company: Optional[str] = None,
        filing_type: Optional[str] = None,
        filing_date: Optional[date] = None,
        cik: Optional[str] = None,
        ticker: Optional[str] = None,
        source_url: Optional[str] = None,
        file_hash: Optional[str] = None,
    ) -> Document:
        doc = Document(
            filename=filename,
            company=company,
            filing_type=filing_type,
            filing_date=filing_date,
            cik=cik,
            ticker=ticker,
            source_url=source_url,
            file_hash=file_hash,
            status="PROCESSING",
        )
        self.session.add(doc)
        await self.session.commit()
        await self.session.refresh(doc)
        return doc

    async def get_by_id(self, doc_id: uuid.UUID) -> Optional[Document]:
        result = await self.session.execute(select(Document).where(Document.id == doc_id))
        return result.scalar_one_or_none()

    async def list_all(self, status: Optional[str] = None) -> list[Document]:
        stmt = select(Document).order_by(Document.created_at.desc())
        if status:
            stmt = stmt.where(Document.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, doc_id: uuid.UUID, status: str, chunk_count: int = 0) -> None:
        await self.session.execute(
            update(Document).where(Document.id == doc_id).values(status=status, chunk_count=chunk_count)
        )
        await self.session.commit()

    async def delete(self, doc_id: uuid.UUID) -> bool:
        doc = await self.get_by_id(doc_id)
        if not doc:
            return False
        await self.session.delete(doc)
        await self.session.commit()
        return True

    async def get_by_hash(self, file_hash: str) -> Optional[Document]:
        result = await self.session.execute(select(Document).where(Document.file_hash == file_hash))
        return result.scalar_one_or_none()
