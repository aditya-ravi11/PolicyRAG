import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from policyrag.ingestion.pipeline import ingest_pdf, compute_file_hash, delete_document_chunks


def test_compute_file_hash():
    h1 = compute_file_hash(b"hello world")
    h2 = compute_file_hash(b"hello world")
    h3 = compute_file_hash(b"different")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64


@pytest.mark.asyncio
async def test_ingest_pdf_from_bytes():
    # Create a minimal PDF-like test
    with patch("policyrag.ingestion.pipeline.extract_text_from_bytes") as mock_extract, \
         patch("policyrag.ingestion.pipeline.embed_texts", new_callable=AsyncMock) as mock_embed, \
         patch("policyrag.ingestion.pipeline.get_collection") as mock_collection:

        mock_extract.return_value = [
            (1, "ITEM 1. BUSINESS\nApple designs smartphones."),
            (2, "ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS\nRevenue was $383B."),
        ]
        mock_embed.return_value = [[0.1] * 384] * 10  # enough for all chunks
        collection = MagicMock()
        mock_collection.return_value = collection

        doc_id, chunk_count = await ingest_pdf(
            pdf_bytes=b"fake pdf bytes",
            doc_id="test-doc",
            company="Apple",
            filing_type="10-K",
        )

        assert doc_id == "test-doc"
        assert chunk_count > 0
        collection.add.assert_called()


@pytest.mark.asyncio
async def test_ingest_pdf_empty_text_raises():
    with patch("policyrag.ingestion.pipeline.extract_text_from_bytes") as mock_extract:
        mock_extract.return_value = []
        with pytest.raises(ValueError, match="No text"):
            await ingest_pdf(pdf_bytes=b"empty", doc_id="test")


def test_delete_document_chunks():
    with patch("policyrag.ingestion.pipeline.get_collection") as mock_collection:
        collection = MagicMock()
        collection.get.return_value = {"ids": ["c1", "c2"]}
        mock_collection.return_value = collection

        delete_document_chunks("doc1")
        collection.delete.assert_called_once_with(ids=["c1", "c2"])


def test_delete_document_chunks_empty():
    with patch("policyrag.ingestion.pipeline.get_collection") as mock_collection:
        collection = MagicMock()
        collection.get.return_value = {"ids": []}
        mock_collection.return_value = collection

        delete_document_chunks("doc1")
        collection.delete.assert_not_called()
