from typing import List
from marker_pdf import MarkerPDF
import fitz  # PyMuPDF

class OCRHandler:
    def __init__(self):
        self.marker = MarkerPDF()

    def is_ocr_needed(self, pdf_path: str) -> bool:
        """Check if OCR is needed by attempting to extract text."""
        try:
            doc = fitz.open(pdf_path)
            # Check first 5 pages for text content
            for page_num in range(min(5, len(doc))):
                page = doc[page_num]
                if len(page.get_text().strip()) > 100:  # If page has substantial text
                    continue
                return True  # OCR needed if any page lacks text
            return False
        except Exception as e:
            print(f"Error checking OCR need: {e}")
            return True  # Assume OCR needed if we can't check

    def process_pages(self, pdf_path: str, max_pages: int = None) -> List[str]:
        """Process PDF pages with OCR."""
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            # Determine pages to process
            if max_pages and total_pages > max_pages:
                pages_to_process = list(range(max_pages))
            else:
                pages_to_process = list(range(total_pages))

            # Process pages
            results = []
            for page_num in pages_to_process:
                page = doc[page_num]
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                
                # Use marker-pdf for OCR
                ocr_result = self.marker.process_image(img_data)
                results.append(ocr_result.text)

            return results

        except Exception as e:
            print(f"Error during OCR processing: {e}")
            return []

    def process_with_page_limit(self, pdf_path: str, page_threshold: int = 50) -> List[str]:
        """Process PDF with OCR, respecting page threshold."""
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # For documents over threshold, only OCR first 5 pages
        max_pages = 5 if total_pages >= page_threshold else total_pages
        return self.process_pages(pdf_path, max_pages)