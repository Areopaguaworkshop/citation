from typing import Dict, Any
import pypdf
import bibtexparser
import os

# Minimal PDF parser for CLI integration
def check_ocr_needed(file_path: str) -> bool:
    """Check if OCR is needed for the PDF."""
    # TODO: Implement OCR detection
    return False

def extract_metadata(file_path: str, page_count: int, page_threshold: int) -> Dict[str, Any]:
    """Extract metadata from PDF using various libraries."""
    metadata = {}
    
    # Try different metadata extraction methods
    try:
        with open(file_path, 'rb') as pdf_file:
            reader = pypdf.PdfReader(pdf_file)
            pdf_info = reader.metadata
            if pdf_info:
                metadata.update({
                    'title': pdf_info.get('/Title', ''),
                    'author': pdf_info.get('/Author', ''),
                    'publisher': pdf_info.get('/Publisher', ''),
                })
    except Exception as e:
        print(f"PDF metadata extraction failed: {e}")

    # Determine document type based on page count
    if page_count >= page_threshold:
        metadata['citation_type'] = 'book' if 'thesis' not in file_path.lower() else 'thesis'
    else:
        metadata['citation_type'] = 'article'  # Default to article, can be refined later

    return metadata

def parse_pdf(file_path: str, page_threshold: int = 50) -> Dict[str, Any]:
    """
    Parse PDF file and extract citation information.
    
    Args:
        file_path: Path to the PDF file
        page_threshold: Page number threshold to differentiate between books and articles
    
    Returns:
        Dictionary containing citation information
    """
    if not os.path.exists(file_path):
        return {
            'type': 'pdf',
            'error': f"File not found: {file_path}",
            'file_path': file_path,
            'citation_type': 'thesis' if 'thesis' in file_path.lower() else 'unknown'
        }
        
    try:
        # Get basic PDF info
        with open(file_path, 'rb') as pdf_file:
            reader = pypdf.PdfReader(pdf_file)
            page_count = len(reader.pages)
            
        # Check if OCR is needed
        if check_ocr_needed(file_path):
            # TODO: Implement OCR using marker-pdf or docling
            pass
            
        # Extract metadata
        metadata = extract_metadata(file_path, page_count, page_threshold)
        
        # Add basic information
        metadata.update({
            'type': 'pdf',
            'pages': f"pp. 1-{page_count}",
            'file_path': file_path
        })
        
        return metadata
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return {
            'type': 'pdf',
            'error': str(e),
            'file_path': file_path,
            'citation_type': 'thesis' if 'thesis' in file_path.lower() else 'unknown'
        }
