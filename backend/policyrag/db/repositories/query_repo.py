import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from policyrag.db.models import QueryCitation


class QueryCitationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_many(self, citations: list[dict]) -> list[QueryCitation]:
        records = [QueryCitation(**c) for c in citations]
        self.session.add_all(records)
        await self.session.commit()
        return records

    async def get_by_query_id(self, query_id: uuid.UUID) -> list[QueryCitation]:
        result = await self.session.execute(
            select(QueryCitation)
            .where(QueryCitation.query_id == query_id)
            .order_by(QueryCitation.citation_index)
        )
        return list(result.scalars().all())
