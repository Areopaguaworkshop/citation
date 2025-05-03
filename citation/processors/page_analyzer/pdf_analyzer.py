from typing import Dict, Any, Optional, Tuple
import fitz  # PyMuPDF
import re

class PDFPageAnalyzer:
    def __init__(self):
        self.title_patterns = [
            r'(?i)^title:?\s*(.+)$',
            r'(?i)^chapter:?\s*(.+)$',
            r'(?i)^phd\s+thesis:?\s*(.+)$',
            r'(?i)^master\s+thesis:?\s*(.+)$'
        ]
        
        self.copyright_patterns = [
            r'(?i)©\s*(\d{4})',
            r'(?i)copyright\s*(\d{4})',
            r'(?i)published\s+(?:by|in)\s+(.+?)(?:\.|,|\n)',
            r'(?i)publisher:?\s*([^\.]+)'
        ]

    def find_key_pages(self, pdf_path: str, max_pages: int = 10) -> Tuple[Optional[int], Optional[int]]:
        """Find the title page and copyright page in a PDF."""
        try:
            doc = fitz.open(pdf_path)
            title_page = None
            copyright_page = None
            
            # Only check first few pages
            for page_num in range(min(max_pages, len(doc))):
                page = doc[page_num]
                text = page.get_text()
                
                # Check for title page characteristics
                if title_page is None and any(re.search(pattern, text, re.MULTILINE) 
                                           for pattern in self.title_patterns):
                    title_page = page_num
                
                # Check for copyright page characteristics
                if copyright_page is None and any(re.search(pattern, text, re.MULTILINE) 
                                               for pattern in self.copyright_patterns):
                    copyright_page = page_num
                    
                if title_page is not None and copyright_page is not None:
                    break
                    
            return title_page, copyright_page
            
        except Exception as e:
            print(f"Error analyzing PDF pages: {e}")
            return None, None

    def extract_page_metadata(self, pdf_path: str, page_num: int) -> Dict[str, Any]:
        """Extract metadata from a specific page."""
        metadata = {}
        try:
            doc = fitz.open(pdf_path)
            if 0 <= page_num < len(doc):
                page = doc[page_num]
                text = page.get_text()
                
                # Extract title
                for pattern in self.title_patterns:
                    match = re.search(pattern, text, re.MULTILINE)
                    if match:
                        metadata['title'] = match.group(1).strip()
                        break
                
                # Extract copyright info
                for pattern in self.copyright_patterns:
                    match = re.search(pattern, text, re.MULTILINE)
                    if match:
                        if 'year' in pattern:
                            metadata['year'] = match.group(1)
                        elif 'publisher' in pattern:
                            metadata['publisher'] = match.group(1).strip()
                
        except Exception as e:
            print(f"Error extracting page metadata: {e}")
            
        return metadata

    def analyze_header_footer(self, pdf_path: str) -> Dict[str, Any]:
        """Analyze headers and footers for journal/conference papers."""
        metadata = {}
        try:
            doc = fitz.open(pdf_path)
            header_texts = []
            footer_texts = []
            
            # Check first few pages
            for page_num in range(min(3, len(doc))):
                page = doc[page_num]
                mediabox = page.mediabox
                
                # Get header region (top 15% of page)
                header_region = fitz.Rect(
                    mediabox.x0, mediabox.y0,
                    mediabox.x1, mediabox.y0 + mediabox.height * 0.15
                )
                header_text = page.get_text("text", clip=header_region)
                header_texts.append(header_text)
                
                # Get footer region (bottom 15% of page)
                footer_region = fitz.Rect(
                    mediabox.x0, mediabox.y1 - mediabox.height * 0.15,
                    mediabox.x1, mediabox.y1
                )
                footer_text = page.get_text("text", clip=footer_region)
                footer_texts.append(footer_text)
            
            # Look for journal name in headers
            journal_patterns = [
                r'(?i)journal\s+of\s+([^\n]+)',
                r'(?i)proceedings\s+of\s+([^\n]+)'
            ]
            
            for text in header_texts:
                for pattern in journal_patterns:
                    match = re.search(pattern, text)
                    if match:
                        metadata['journal'] = match.group(1).strip()
                        break
                if 'journal' in metadata:
                    break
            
            # Look for conference name in footers
            conf_patterns = [
                r'(?i)proceedings?\s+of\s+([^\n]+\d{4})',
                r'(?i)(\d{4}\s+\w+\s+conference)'
            ]
            
            for text in footer_texts:
                for pattern in conf_patterns:
                    match = re.search(pattern, text)
                    if match:
                        metadata['conference'] = match.group(1).strip()
                        break
                if 'conference' in metadata:
                    break
                        
        except Exception as e:
            print(f"Error analyzing headers/footers: {e}")
            
        return metadata