"""
Citation extraction tool for PDF files and URLs.
Supports Chicago Author-Date style citations.
"""

from .main import CitationExtractor
from .model import CitationLLM
from .utils import get_input_type
from .citation_style import format_bibliography

__version__ = "0.10.0"
__all__ = [
    "CitationExtractor",
    "CitationLLM",
    "get_input_type",
    "format_bibliography",
]
