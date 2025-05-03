from pathlib import Path
from typing import Union, Dict, Any, Optional
import argparse
import sys
import asyncio
from model import pdf_search
from form import CitationsForBook, CitationsForThesis
from .core.document_type.detector import DocumentDetector
from .core.ocr.handler import OCRHandler
from .processors.metadata.extractor import MetadataExtractor
from .processors.page_analyzer.pdf_analyzer import PDFPageAnalyzer
from .llm.models.llm_handler import LLMHandler
from .output.formatters.citation_formatter import CitationFormatter
from .schemas.citation_types.schemas import validate_citation

class Citation:
    def __init__(self, page_threshold: int = 50, citation_style: str = "chicago"):
        self.page_threshold = page_threshold
        self.citation_style = citation_style
        self.detector = DocumentDetector(page_threshold=page_threshold)
        self.ocr_handler = OCRHandler()
        self.metadata_extractor = MetadataExtractor()
        self.pdf_analyzer = PDFPageAnalyzer()
        self.llm_handler = LLMHandler()
        self.formatter = CitationFormatter(style=citation_style)

    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a document and extract citation information."""
        # Detect document type
        doc_type = self.detector.detect_type(file_path)
        
        # Initialize metadata with basic info
        metadata = {
            'type': doc_type,
            'file_path': file_path,
            'citation_style': self.citation_style
        }
        
        # Process based on document type
        if doc_type == 'pdf':
            metadata = await self._process_pdf(file_path, metadata)
        elif doc_type == 'url':
            metadata = await self._process_url(file_path, metadata)
        else:  # video or audio
            metadata = await self._process_media(file_path, metadata)
            
        # Validate final metadata
        validated_metadata = validate_citation(metadata)
        return validated_metadata

    async def _process_pdf(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process PDF document."""
        # Check if OCR is needed
        if self.ocr_handler.is_ocr_needed(file_path):
            ocr_text = self.ocr_handler.process_with_page_limit(file_path, self.page_threshold)
        else:
            ocr_text = []
        
        # Find key pages
        title_page, copyright_page = self.pdf_analyzer.find_key_pages(file_path)
        
        # Extract metadata from PDF
        pdf_metadata = self.metadata_extractor.extract_from_pdf(file_path)
        metadata.update(pdf_metadata)
        
        # Extract metadata from key pages if found
        if title_page is not None:
            title_metadata = self.pdf_analyzer.extract_page_metadata(file_path, title_page)
            metadata.update(title_metadata)
            
        if copyright_page is not None:
            copyright_metadata = self.pdf_analyzer.extract_page_metadata(file_path, copyright_page)
            metadata.update(copyright_metadata)
            
        # For shorter documents, analyze headers/footers
        if metadata.get('page_count', 0) < self.page_threshold:
            header_footer_metadata = self.pdf_analyzer.analyze_header_footer(file_path)
            metadata.update(header_footer_metadata)
        
        # Use LLM to enhance metadata
        enhanced_metadata = await self.llm_handler.enhance_metadata(
            "\n".join(ocr_text) if ocr_text else "",
            'pdf',
            metadata
        )
        
        return enhanced_metadata

    async def _process_url(self, url: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process URL."""
        import httpx
        import bs4
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            html_content = response.text
            
        # Extract metadata from URL
        url_metadata = self.metadata_extractor.extract_from_url(url, html_content)
        metadata.update(url_metadata)
        
        # Use LLM to enhance metadata
        soup = bs4.BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text()
        enhanced_metadata = await self.llm_handler.enhance_metadata(
            text_content,
            'url',
            metadata
        )
        
        return enhanced_metadata

    async def _process_media(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process video or audio file."""
        try:
            import moviepy.editor as mp
            
            # Extract basic media info
            if metadata['type'] == 'video':
                clip = mp.VideoFileClip(file_path)
            else:
                clip = mp.AudioFileClip(file_path)
                
            duration = clip.duration
            media_info = {
                'duration': f"{int(duration//3600):02d}:{int((duration%3600)//60):02d}:{int(duration%60):02d}"
            }
            clip.close()
            
            # Extract metadata
            media_metadata = self.metadata_extractor.extract_from_media(file_path, media_info)
            metadata.update(media_metadata)
            
            # Use LLM to enhance metadata
            enhanced_metadata = await self.llm_handler.enhance_metadata(
                f"Media file: {Path(file_path).name}, Duration: {media_info['duration']}",
                metadata['type'],
                metadata
            )
            
            return enhanced_metadata
            
        except Exception as e:
            print(f"Error processing media file: {e}")
            return metadata

    def save_citation(self, metadata: Dict[str, Any], output_path: str, output_format: str = 'yaml') -> None:
        """Save citation to file."""
        self.formatter.save_to_file(metadata, output_path, output_format)

    async def get_formatted_citation(self, metadata: Dict[str, Any]) -> str:
        """Get formatted citation string."""
        return await self.llm_handler.format_citation(metadata, self.citation_style)

def process_pdf(pdf_path: str) -> Union[CitationsForBook, CitationsForThesis]:
    """
    Process a PDF file and return citation information.
    
    Args:
        pdf_path: Path to the PDF file
    Returns:
        Citation object (either book or thesis)
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    if path.suffix.lower() != '.pdf':
        raise ValueError(f"File must be a PDF: {pdf_path}")
    
    return pdf_search(str(path))

def main():
    parser = argparse.ArgumentParser(
        description="Extract citation information from PDF documents"
    )
    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to the PDF file"
    )
    
    args = parser.parse_args()
    
    try:
        citation = process_pdf(args.pdf_path)
        print(f"\nCitation Information:")
        for field in citation.__dataclass_fields__:
            value = getattr(citation, field)
            if value is not None:
                print(f"{field}: {value}")
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
