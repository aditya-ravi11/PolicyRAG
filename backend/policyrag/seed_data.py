"""Seed demo data: download sample SEC filings and run ingestion."""
import asyncio
import logging

from policyrag.db.session import async_session_factory
from policyrag.db.repositories.document_repo import DocumentRepository
from policyrag.ingestion.edgar_client import download_filing
from policyrag.ingestion.pipeline import compute_file_hash, ingest_pdf

logger = logging.getLogger(__name__)

DEMO_FILINGS = [
    {"ticker": "AAPL", "filing_type": "10-K", "company": "Apple Inc."},
    {"ticker": "JPM", "filing_type": "10-K", "company": "JPMorgan Chase & Co."},
    {"ticker": "TSLA", "filing_type": "10-Q", "company": "Tesla, Inc."},
]


async def seed_demo_data():
    """Download and ingest demo filings if not already present."""
    async with async_session_factory() as session:
        repo = DocumentRepository(session)
        existing = await repo.list_all()

        if existing:
            logger.info(f"Found {len(existing)} existing documents, skipping seed")
            return

    logger.info("Seeding demo data...")
    for filing_info in DEMO_FILINGS:
        ticker = filing_info["ticker"]
        filing_type = filing_info["filing_type"]
        company = filing_info["company"]

        try:
            logger.info(f"Downloading {ticker} {filing_type}...")
            filings = await download_filing(
                ticker=ticker,
                filing_type=filing_type,
                max_filings=1,
            )

            for filing in filings:
                content = filing["content"]
                meta = filing["metadata"]
                file_hash = compute_file_hash(content)

                async with async_session_factory() as session:
                    repo = DocumentRepository(session)
                    existing = await repo.get_by_hash(file_hash)
                    if existing:
                        logger.info(f"Filing already exists: {ticker}")
                        continue

                    from datetime import date
                    fd = None
                    try:
                        fd = date.fromisoformat(meta["filing_date"])
                    except (ValueError, KeyError):
                        pass

                    doc = await repo.create(
                        filename=filing["filename"],
                        company=company,
                        filing_type=filing_type,
                        filing_date=fd,
                        cik=meta.get("cik"),
                        ticker=ticker,
                        source_url=meta.get("source_url"),
                        file_hash=file_hash,
                    )

                    try:
                        _, chunk_count = await ingest_pdf(
                            pdf_bytes=content,
                            doc_id=str(doc.id),
                            company=company,
                            filing_type=filing_type,
                            filing_date=meta.get("filing_date"),
                        )
                        await repo.update_status(doc.id, "READY", chunk_count)
                        logger.info(f"Ingested {ticker}: {chunk_count} chunks")
                    except Exception as e:
                        logger.error(f"Ingestion failed for {ticker}: {e}")
                        await repo.update_status(doc.id, "FAILED")

        except Exception as e:
            logger.error(f"Failed to download {ticker}: {e}")
            continue

    logger.info("Seed data complete")


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
