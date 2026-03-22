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


def _build_page_lookup(pages: list[tuple[int, str]]) -> list[tuple[int, int]]:
    """Build a list of (char_offset, page_num) for the concatenated full text.

    Returns sorted list so we can binary-search for the page of any char offset.
    """
    entries = []
    offset = 0
    for page_num, text in pages:
        entries.append((offset, page_num))
        offset += len(text) + 2  # +2 for the \n\n join separator
    return entries


def _find_page(page_lookup: list[tuple[int, int]], char_offset: int) -> int:
    """Find the page number for a given character offset using binary search."""
    result = 1
    for off, pn in page_lookup:
        if off <= char_offset:
            result = pn
        else:
            break
    return result


async def ingest_pdf(
    pdf_path: Optional[str] = None,
    pdf_bytes: Optional[bytes] = None,
    doc_id: Optional[str] = None,
    company: Optional[str] = None,
    filing_type: Optional[str] = None,
    filing_date: Optional[str] = None,
    user_id: Optional[str] = None,
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

    # Build page lookup for accurate per-chunk page assignment
    page_lookup = _build_page_lookup(pages)

    # Split into sections
    sections = split_sections(full_text)
    logger.info(f"Document split into {len(sections)} sections for doc {doc_id}")

    # Chunk each section
    all_chunks: list[Chunk] = []
    for section in sections:
        # Find the page for this section's start
        section_page = _find_page(page_lookup, section.start_idx)

        chunks = chunk_text(
            text=section.text,
            doc_id=doc_id,
            section=section.name,
            page_num=section_page,
            company=company,
            filing_type=filing_type,
            filing_date=filing_date,
            user_id=user_id,
        )

        # For each chunk, try to assign a more accurate page by finding
        # the chunk's approximate offset within the full text
        for i, chunk in enumerate(chunks):
            # Estimate the chunk's position in the full text
            chunk_offset_in_section = section.text.find(chunk.text[:80])
            if chunk_offset_in_section >= 0:
                abs_offset = section.start_idx + chunk_offset_in_section
                chunk.metadata["page_num"] = _find_page(page_lookup, abs_offset)

        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError("No chunks produced from PDF")

    # Prepend section context to chunk text for better embeddings
    # This helps the embedding model understand the chunk's context
    texts_for_embedding = []
    for chunk in all_chunks:
        section_prefix = f"[{chunk.metadata.get('section', 'Unknown')}] "
        texts_for_embedding.append(section_prefix + chunk.text)

    # Embed (using section-prefixed text for better semantic search)
    embeddings = await embed_texts(texts_for_embedding)

    # Store in ChromaDB — store the original chunk text (without prefix) as the document
    # but use the prefixed embedding for retrieval
    collection = get_collection()
    ids = [f"{doc_id}_{i}" for i in range(len(all_chunks))]
    raw_texts = [c.text for c in all_chunks]
    metadatas = [c.metadata for c in all_chunks]

    # ChromaDB has batch size limits; upload in batches of 500
    batch_size = 500
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        collection.add(
            ids=ids[i:end],
            documents=raw_texts[i:end],
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
