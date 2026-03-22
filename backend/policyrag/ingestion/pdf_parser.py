import logging

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFParseError(Exception):
    """Raised when a PDF cannot be parsed."""


def extract_text_from_pdf(pdf_path: str) -> list[tuple[int, str]]:
    """Extract text from PDF, returns list of (page_num, text) tuples."""
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise PDFParseError(f"Cannot open PDF file: {e}") from e

    if doc.is_encrypted:
        doc.close()
        raise PDFParseError("PDF is encrypted and cannot be read")

    if doc.page_count == 0:
        doc.close()
        raise PDFParseError("PDF has no pages")

    pages = []
    for page_num in range(len(doc)):
        try:
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                pages.append((page_num + 1, text))
        except Exception as e:
            logger.warning(f"Failed to extract page {page_num + 1}: {e}")
    doc.close()

    if not pages:
        raise PDFParseError("PDF contains no extractable text (possibly scanned/image-only)")

    return pages


def extract_text_from_bytes(pdf_bytes: bytes) -> list[tuple[int, str]]:
    """Extract text from PDF bytes, returns list of (page_num, text) tuples."""
    if not pdf_bytes:
        raise PDFParseError("Empty PDF content")

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise PDFParseError(f"Cannot parse PDF bytes: {e}") from e

    if doc.is_encrypted:
        doc.close()
        raise PDFParseError("PDF is encrypted and cannot be read")

    if doc.page_count == 0:
        doc.close()
        raise PDFParseError("PDF has no pages")

    pages = []
    for page_num in range(len(doc)):
        try:
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                pages.append((page_num + 1, text))
        except Exception as e:
            logger.warning(f"Failed to extract page {page_num + 1}: {e}")
    doc.close()

    if not pages:
        raise PDFParseError("PDF contains no extractable text (possibly scanned/image-only)")

    return pages
