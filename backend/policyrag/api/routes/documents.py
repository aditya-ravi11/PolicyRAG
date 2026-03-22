import logging
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from policyrag.api.deps import get_cache, get_db
from policyrag.auth.jwt_verifier import get_current_user
from policyrag.auth.storage import delete_from_storage, upload_to_storage
from policyrag.cache.redis_cache import QueryCache
from policyrag.db.repositories.document_repo import DocumentRepository
from policyrag.ingestion.edgar_client import download_filing
from policyrag.ingestion.pipeline import compute_file_hash, delete_document_chunks, ingest_pdf
from policyrag.schemas.document import DocumentResponse, EdgarRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


async def _run_ingestion(
    doc_id: str,
    pdf_bytes: bytes,
    company: Optional[str],
    filing_type: Optional[str],
    filing_date: Optional[str],
    db_url: str,
    user_id: Optional[str] = None,
):
    """Background task for PDF ingestion."""
    from policyrag.db.session import async_session_factory

    try:
        _, chunk_count = await ingest_pdf(
            pdf_bytes=pdf_bytes,
            doc_id=doc_id,
            company=company,
            filing_type=filing_type,
            filing_date=filing_date,
            user_id=user_id,
        )
        async with async_session_factory() as session:
            repo = DocumentRepository(session)
            await repo.update_status(uuid.UUID(doc_id), "READY", chunk_count)
    except Exception as e:
        logger.error(f"Ingestion failed for {doc_id}: {e}", exc_info=True)
        try:
            async with async_session_factory() as session:
                repo = DocumentRepository(session)
                await repo.update_status(uuid.UUID(doc_id), "FAILED")
        except Exception as db_err:
            logger.error(f"Failed to update status to FAILED for {doc_id}: {db_err}")


@router.post("", response_model=DocumentResponse, summary="Upload PDF document", description="Upload a PDF filing for ingestion. The file is processed asynchronously.")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    company: Optional[str] = Form(None),
    filing_type: Optional[str] = Form(None),
    filing_date: Optional[str] = Form(None),
    ticker: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()

    # PDF size limit: 50 MB
    max_size = 50 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"PDF too large ({len(content) / (1024*1024):.1f} MB). Maximum size is 50 MB.",
        )
    file_hash = compute_file_hash(content)
    user_id = user["user_id"]

    repo = DocumentRepository(db)
    existing = await repo.get_by_hash(file_hash, user_id=user_id)
    if existing:
        return DocumentResponse(
            id=str(existing.id),
            filename=existing.filename,
            company=existing.company,
            filing_type=existing.filing_type,
            filing_date=existing.filing_date,
            ticker=existing.ticker,
            status=existing.status,
            chunk_count=existing.chunk_count,
            created_at=existing.created_at,
        )

    from datetime import date as date_type
    fd = None
    if filing_date:
        try:
            fd = date_type.fromisoformat(filing_date)
        except ValueError:
            pass

    doc = await repo.create(
        filename=file.filename,
        user_id=user_id,
        company=company,
        filing_type=filing_type,
        filing_date=fd,
        ticker=ticker,
        file_hash=file_hash,
    )

    # Upload to Supabase Storage
    try:
        upload_to_storage(user_id, str(doc.id), file.filename, content)
    except Exception as e:
        logger.warning(f"Storage upload failed (non-critical): {e}")

    from policyrag.config import settings
    background_tasks.add_task(
        _run_ingestion,
        str(doc.id), content, company, filing_type, filing_date, settings.DATABASE_URL,
        user_id=user_id,
    )

    return DocumentResponse(
        id=str(doc.id),
        filename=doc.filename,
        company=doc.company,
        filing_type=doc.filing_type,
        filing_date=doc.filing_date,
        ticker=doc.ticker,
        status=doc.status,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at,
    )


@router.post("/edgar", response_model=list[DocumentResponse], summary="Fetch from EDGAR", description="Download SEC filings from EDGAR by ticker symbol and filing type.")
async def fetch_edgar(
    request: EdgarRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    try:
        filings = await download_filing(
            ticker=request.ticker,
            filing_type=request.filing_type,
            date_after=request.date_after,
            date_before=request.date_before,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    user_id = user["user_id"]
    results = []
    repo = DocumentRepository(db)
    for filing in filings:
        meta = filing["metadata"]
        content = filing["content"]
        file_hash = compute_file_hash(content)

        existing = await repo.get_by_hash(file_hash, user_id=user_id)
        if existing:
            results.append(DocumentResponse(
                id=str(existing.id),
                filename=existing.filename,
                company=existing.company,
                filing_type=existing.filing_type,
                filing_date=existing.filing_date,
                ticker=existing.ticker,
                status=existing.status,
                chunk_count=existing.chunk_count,
                created_at=existing.created_at,
            ))
            continue

        from datetime import date as date_type
        fd = None
        try:
            fd = date_type.fromisoformat(meta["filing_date"])
        except (ValueError, KeyError):
            pass

        doc = await repo.create(
            filename=filing["filename"],
            user_id=user_id,
            company=meta.get("ticker", request.ticker).upper(),
            filing_type=meta.get("filing_type", request.filing_type),
            filing_date=fd,
            cik=meta.get("cik"),
            ticker=meta.get("ticker", request.ticker).upper(),
            source_url=meta.get("source_url"),
            file_hash=file_hash,
        )

        background_tasks.add_task(
            _run_ingestion,
            str(doc.id), content, doc.company, doc.filing_type,
            meta.get("filing_date"), "unused",
            user_id=user_id,
        )
        results.append(DocumentResponse(
            id=str(doc.id),
            filename=doc.filename,
            company=doc.company,
            filing_type=doc.filing_type,
            filing_date=doc.filing_date,
            ticker=doc.ticker,
            status=doc.status,
            chunk_count=doc.chunk_count,
            created_at=doc.created_at,
        ))

    return results


@router.get("", response_model=list[DocumentResponse], summary="List documents", description="List all ingested documents, optionally filtered by processing status.")
async def list_documents(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    repo = DocumentRepository(db)
    docs = await repo.list_all(user_id=user["user_id"], status=status)
    return [
        DocumentResponse(
            id=str(d.id), filename=d.filename, company=d.company,
            filing_type=d.filing_type, filing_date=d.filing_date, ticker=d.ticker,
            status=d.status, chunk_count=d.chunk_count, created_at=d.created_at,
        )
        for d in docs
    ]


@router.get("/{doc_id}", response_model=DocumentResponse, summary="Get document", description="Retrieve a single document by its ID.")
async def get_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    repo = DocumentRepository(db)
    doc = await repo.get_by_id(uuid.UUID(doc_id), user_id=user["user_id"])
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(
        id=str(doc.id), filename=doc.filename, company=doc.company,
        filing_type=doc.filing_type, filing_date=doc.filing_date, ticker=doc.ticker,
        status=doc.status, chunk_count=doc.chunk_count, created_at=doc.created_at,
    )


@router.delete("/{doc_id}", summary="Delete document", description="Delete a document and its associated chunks from the vector store and cache.")
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    cache: QueryCache = Depends(get_cache),
    user: dict = Depends(get_current_user),
):
    user_id = user["user_id"]
    repo = DocumentRepository(db)
    doc = await repo.get_by_id(uuid.UUID(doc_id), user_id=user_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from Supabase Storage
    storage_path = f"{user_id}/{doc_id}/{doc.filename}"
    try:
        delete_from_storage(storage_path)
    except Exception as e:
        logger.warning(f"Storage delete failed (non-critical): {e}")

    delete_document_chunks(doc_id)
    await repo.delete(uuid.UUID(doc_id), user_id=user_id)
    await cache.invalidate_for_document(doc_id)

    return {"status": "deleted"}


@router.get("/{doc_id}/chunks", summary="Get document chunks", description="Retrieve all text chunks for a document from the vector store.")
async def get_document_chunks(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    # Verify ownership
    repo = DocumentRepository(db)
    doc = await repo.get_by_id(uuid.UUID(doc_id), user_id=user["user_id"])
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    from policyrag.ingestion.pipeline import get_collection
    collection = get_collection()
    results = collection.get(where={"doc_id": doc_id}, include=["documents", "metadatas"])
    chunks = []
    for i, chunk_id in enumerate(results["ids"]):
        chunks.append({
            "id": chunk_id,
            "text": results["documents"][i],
            "metadata": results["metadatas"][i],
        })
    return chunks
