from enum import Enum
from pathlib import Path
from typing import Type, Union, Optional, List
import fitz  # PyMuPDF
from marker.converters.pdf import PdfConverter # Change to correct import
import tempfile
import os
from form import (
    CitationsForBook,
    CitationsForArticle,
    CitationsForUrl,
    CitationsForLecture,
    CitationsForThesis
)

class FileType(Enum):
    PDF = "pdf"
    VIDEO = "video"
    AUDIO = "audio"
    URL = "url"

def get_file_type(file_path: str) -> FileType:
    ext = Path(file_path).suffix.lower()
    if ext == '.pdf':
        return FileType.PDF
    elif ext in ['.mp4', '.avi', '.mov', '.webm']:
        return FileType.VIDEO
    elif ext in ['.mp3', '.wav', '.ogg']:
        return FileType.AUDIO
    else:
        return FileType.URL

def count_pdf_pages(file_path: str) -> Optional[int]:
    """Count pages in a PDF file using PyMuPDF."""
    try:
        with fitz.open(file_path) as pdf_doc:
            return pdf_doc.page_count
    except Exception:
        return None

def input_class(file_path: str, pdf_pages: Optional[int] = None) -> Type[Union[CitationsForBook, CitationsForArticle, CitationsForLecture, CitationsForUrl, CitationsForThesis]]:
    file_type = get_file_type(file_path)
    
    if file_type == FileType.PDF:
        if pdf_pages is None:
            pdf_pages = count_pdf_pages(file_path)
        if pdf_pages is not None and pdf_pages <= 50:
            return CitationsForArticle
        return [CitationsForBook, CitationsForArticle, CitationsForThesis]
    elif file_type in [FileType.VIDEO, FileType.AUDIO]:
        return CitationsForLecture
    else:  # URL
        return [CitationsForUrl, CitationsForLecture]

def pdf_md(file_path: str, head_pages: int = 15, tail_pages: int = 10) -> str:
    """
    Convert PDF to markdown with OCR support for non-OCRed pages.
    Increased page range for better Chinese content detection.
    """
    try:
        pdf_doc = fitz.open(file_path)
        total_pages = pdf_doc.page_count
        markdown_parts = []

        # Increase pages to process for better content capture
        head_range = range(min(head_pages, total_pages))
        tail_range = range(max(0, total_pages - tail_pages), total_pages)
        pages_to_process = sorted(set(list(head_range) + list(tail_range)))

        for page_num in pages_to_process:
            page = pdf_doc[page_num]
            
            # Try to get text with different encoding handling
            text = page.get_text()
            if not text.strip():
                # If no text, use marker-pdf for OCR with Chinese language support
                text = processor.get_page_text(page_num, lang='chi_sim+eng')
            
            # Clean up the text and maintain Chinese characters
            text = text.strip().replace('\x00', '')
            
            markdown_parts.append(f"--page {page_num + 1}--\n\n{text}\n\n")

        pdf_doc.close()
        return "".join(markdown_parts)

    except Exception as e:
        return f"Error processing PDF: {str(e)}"
