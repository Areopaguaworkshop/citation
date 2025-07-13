"""
Citation extraction tool for PDF files and URLs.
Supports Chicago Author-Date style citations.
"""

from .main import CitationExtractor, get_pdf_citation_text

__version__ = "0.1.0"
__all__ = ["CitationExtractor", "get_pdf_citation_text"]

def hello() -> str:
    return "Hello from citation!"
