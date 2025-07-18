"""
Citation extraction tool for PDF files and URLs.
Supports Chicago Author-Date style citations.
"""

from .main import CitationExtractor
from .model import CitationLLM
from .utils import is_url, is_pdf_file, is_media_file
from .citation_style import format_bibliography

__version__ = "0.10.0"
__all__ = [
    "CitationExtractor",
    "CitationLLM",
    "is_url",
    "is_pdf_file",
    "is_media_file",
    "format_bibliography",
]
