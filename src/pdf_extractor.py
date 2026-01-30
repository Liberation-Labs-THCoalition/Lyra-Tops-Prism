"""PDF text extraction using PyMuPDF."""

import fitz  # PyMuPDF
from pathlib import Path
import config


def extract_text(pdf_path: str) -> str:
    """Extract full text from a PDF file.

    Checks for cached full_text.txt first.
    After extraction, caches the result.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text content
    """
    pdf_path = Path(pdf_path)
    cache_path = pdf_path.parent / "full_text.txt"

    # Check cache
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    # Extract
    doc = fitz.open(str(pdf_path))
    text_parts = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text_parts.append(page.get_text())
    doc.close()

    full_text = "\n\n".join(text_parts)

    # Cache
    cache_path.write_text(full_text, encoding="utf-8")

    return full_text
