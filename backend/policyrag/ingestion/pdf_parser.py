import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str) -> list[tuple[int, str]]:
    """Extract text from PDF, returns list of (page_num, text) tuples."""
    pages = []
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            pages.append((page_num + 1, text))
    doc.close()
    return pages


def extract_text_from_bytes(pdf_bytes: bytes) -> list[tuple[int, str]]:
    """Extract text from PDF bytes, returns list of (page_num, text) tuples."""
    pages = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            pages.append((page_num + 1, text))
    doc.close()
    return pages
