from typing import Dict, Any, Optional
import bibtexparser
from datetime import datetime
from pypdf import PdfReader
import re

class MetadataExtractor:
    def __init__(self):
        self.bibtex_parser = bibtexparser.BibtexParser()

    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF using various libraries."""
        metadata = {}
        
        try:
            # Try PyPDF first
            with open(pdf_path, 'rb') as pdf_file:
                reader = PdfReader(pdf_file)
                pdf_info = reader.metadata
                if pdf_info:
                    metadata.update({
                        'title': pdf_info.get('/Title', ''),
                        'author': pdf_info.get('/Author', ''),
                        'publisher': pdf_info.get('/Publisher', ''),
                        'date': pdf_info.get('/CreationDate', ''),
                        'page_count': len(reader.pages)
                    })
                    
            # Clean up date format
            if metadata.get('date'):
                date_match = re.search(r'D:(\d{4})(\d{2})?(\d{2})?', metadata['date'])
                if date_match:
                    year = date_match.group(1)
                    month = date_match.group(2) or '01'
                    day = date_match.group(3) or '01'
                    metadata['year'] = year
                    metadata['date'] = f"{year}-{month}-{day}"

        except Exception as e:
            print(f"PyPDF metadata extraction failed: {e}")

        return metadata

    def extract_from_url(self, url: str, html_content: str) -> Dict[str, Any]:
        """Extract metadata from URL and its HTML content."""
        metadata = {
            'type': 'url',
            'url': url,
            'date_accessed': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Extract metadata from HTML meta tags
        meta_patterns = {
            'title': r'<meta\s+(?:[^>]*?\s+)?property="og:title"\s+content="([^"]*)"',
            'author': r'<meta\s+(?:[^>]*?\s+)?name="author"\s+content="([^"]*)"',
            'date': r'<meta\s+(?:[^>]*?\s+)?property="article:published_time"\s+content="([^"]*)"',
            'publisher': r'<meta\s+(?:[^>]*?\s+)?property="og:site_name"\s+content="([^"]*)"'
        }
        
        for key, pattern in meta_patterns.items():
            match = re.search(pattern, html_content)
            if match:
                metadata[key] = match.group(1)
                
        # Extract year from date if present
        if metadata.get('date'):
            year_match = re.search(r'(\d{4})', metadata['date'])
            if year_match:
                metadata['year'] = year_match.group(1)
                
        return metadata

    def extract_from_media(self, file_path: str, media_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from video/audio file."""
        metadata = {
            'type': 'video' if file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')) else 'audio',
            'file_path': file_path,
            'date_accessed': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Update with media info
        if media_info:
            metadata.update({
                'title': media_info.get('title', ''),
                'lecturer': media_info.get('artist', ''),  # Often stored as artist in media files
                'date': media_info.get('date', ''),
                'publisher': media_info.get('publisher', ''),
                'timeperiod': media_info.get('duration', ''),
                'location': media_info.get('location', '')
            })
            
        return metadata

    def clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize metadata fields."""
        cleaned = {}
        
        for key, value in metadata.items():
            if isinstance(value, str):
                # Remove extra whitespace and normalize
                cleaned[key] = ' '.join(value.split())
                
                # Convert empty strings to None
                if not cleaned[key]:
                    cleaned[key] = None
            else:
                cleaned[key] = value
                
        return cleaned