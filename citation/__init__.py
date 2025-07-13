"""
Citation extraction tool for PDF files and URLs.
Supports Chicago Author-Date style citations.
"""

from .main import CitationExtractor, get_pdf_citation_text
from .model import CitationLLM
from .utils import is_url, is_pdf_file

__version__ = "0.1.0"
__all__ = ["CitationExtractor", "CitationLLM", "get_pdf_citation_text", "is_url", "is_pdf_file"]

def hello() -> str:
    return "Hello from citation!"
