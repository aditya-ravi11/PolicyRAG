import hashlib
import logging
import uuid
from typing import Optional

import chromadb

from policyrag.config import settings
from policyrag.ingestion.chunker import Chunk, chunk_text
from policyrag.ingestion.embedder import embed_texts
from policyrag.ingestion.pdf_parser import extract_text_from_bytes, extract_text_from_pdf
from policyrag.ingestion.sec_section_splitter import split_sections

logger = logging.getLogger(__name__)


def _get_chroma_client() -> chromadb.ClientAPI:
    if settings.CHROMA_HOST:
        return chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    return chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)


def get_collection() -> chromadb.Collection:
    client = _get_chroma_client()
    return client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


async def ingest_pdf(
    pdf_path: Optional[str] = None,
    pdf_bytes: Optional[bytes] = None,
    doc_id: Optional[str] = None,
    company: Optional[str] = None,
    filing_type: Optional[str] = None,
    filing_date: Optional[str] = None,
) -> tuple[str, int]:
    """Ingest a PDF into ChromaDB. Returns (doc_id, chunk_count)."""
    if doc_id is None:
        doc_id = str(uuid.uuid4())

    # Extract text
    if pdf_bytes:
        pages = extract_text_from_bytes(pdf_bytes)
    elif pdf_path:
        pages = extract_text_from_pdf(pdf_path)
    else:
        raise ValueError("Must provide pdf_path or pdf_bytes")

    full_text = "\n\n".join(text for _, text in pages)
    if not full_text.strip():
        raise ValueError("No text extracted from PDF")

    # Build page index for mapping
    page_map = {}
    offset = 0
    for page_num, text in pages:
        page_map[offset] = page_num
        offset += len(text) + 2  # +2 for \n\n

    # Split into sections
    sections = split_sections(full_text)

    # Chunk each section
    all_chunks: list[Chunk] = []
    for section in sections:
        # Find the closest page number
        closest_page = 1
        for off, pn in sorted(page_map.items()):
            if off <= section.start_idx:
                closest_page = pn

        chunks = chunk_text(
            text=section.text,
            doc_id=doc_id,
            section=section.name,
            page_num=closest_page,
            company=company,
            filing_type=filing_type,
            filing_date=filing_date,
        )
        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError("No chunks produced from PDF")

    # Embed
    texts = [c.text for c in all_chunks]
    embeddings = await embed_texts(texts)

    # Store in ChromaDB
    collection = get_collection()
    ids = [f"{doc_id}_{i}" for i in range(len(all_chunks))]
    metadatas = [c.metadata for c in all_chunks]

    # ChromaDB has batch size limits; upload in batches of 500
    batch_size = 500
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        collection.add(
            ids=ids[i:end],
            documents=texts[i:end],
            embeddings=embeddings[i:end],
            metadatas=metadatas[i:end],
        )

    logger.info(f"Ingested {len(all_chunks)} chunks for doc {doc_id}")
    return doc_id, len(all_chunks)


def compute_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def delete_document_chunks(doc_id: str) -> None:
    """Remove all chunks for a document from ChromaDB."""
    collection = get_collection()
    # Get all IDs for this document
    results = collection.get(where={"doc_id": doc_id})
    if results["ids"]:
        collection.delete(ids=results["ids"])
