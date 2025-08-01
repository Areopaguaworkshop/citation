import trafilatura
import os
import subprocess
import logging
import json
import fitz  # PyMuPDF
from datetime import datetime
from typing import Dict, Optional
import tempfile
from pymediainfo import MediaInfo
import asyncio
from crawl4ai import AsyncWebCrawler
import yt_dlp
from .vertical_handler import is_pdf_vertical, process_vertical_pdf
from .vertical_llm import VerticalCitationLLM


from .utils import (
    clean_url,
    extract_publisher_from_domain,
    is_url,
    is_pdf_file,
    is_media_file,
    ensure_searchable_pdf,
    extract_pdf_text,
    determine_url_type,
    save_citation,
    to_csl_json,
    create_subset_pdf,
)
from .type_judge import determine_document_type
from .model import CitationLLM

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Essential Fields for Early Exit ---
ESSENTIAL_FIELDS = {
    "book": ["title", "author", "year", "publisher"],
    "thesis": ["title", "author", "year", "publisher", "genre"],
    "journal": ["title", "author", "container-title", "year", "page_numbers"], # volume/issue handled separately
    "bookchapter": ["title", "author", "container-title", "editor", "publisher", "page_numbers"],
}


def _has_all_essential_fields(citation_info: Dict, doc_type: str) -> bool:
    """Check if all essential fields for the doc type are present."""
    required_fields = ESSENTIAL_FIELDS.get(doc_type, [])
    has_required = all(field in citation_info for field in required_fields)

    if not has_required:
        return False

    if doc_type == "journal":
        # For journals, we also need at least a volume or an issue number.
        return "volume" in citation_info or "issue" in citation_info

    return True


class CitationExtractor:
    def __init__(self, llm_model="ollama/qwen3"):
        """Initialize the citation extractor."""
        self.llm = CitationLLM(llm_model)

    def extract_citation(
        self,
        input_source: str,
        output_dir: str = "example",
        doc_type_override: Optional[str] = None,
        lang: str = "auto",
        text_direction: str = "horizontal",
        vertical_lang: str = "ch",
        page_range: str = "1-5, -3",
    ) -> Optional[Dict]:
        """Main function to extract citation from either PDF or URL."""
        try:
            # Validate input
            if not input_source or not input_source.strip():
                logging.error("Input source is empty or None")
                return None

            # Auto-detect input type with improved error handling
            if is_url(input_source):
                logging.info(f"Detected URL input: {input_source}")
                return self.extract_from_url(input_source, output_dir)
            elif is_pdf_file(input_source):
                logging.info(f"Detected PDF input: {input_source}")
                return self.extract_from_pdf(
                    input_source,
                    output_dir,
                    doc_type_override,
                    lang,
                    text_direction,
                    vertical_lang,
                    page_range,
                )
            elif is_media_file(input_source):
                logging.info(f"Detected media file input: {input_source}")
                return self.extract_from_media_file(input_source, output_dir)
            else:
                logging.error(f"Unknown or unsupported input type: {input_source}")
                if os.path.exists(input_source):
                    logging.error(f"File exists but is not a supported format")
                else:
                    logging.error(f"File does not exist: {input_source}")
                return None
        except Exception as e:
            logging.error(f"Error in citation extraction: {e}")
            import traceback

            logging.debug(traceback.format_exc())
            return None

    def extract_from_pdf(
        self,
        input_pdf_path: str,
        output_dir: str = "example",
        doc_type_override: Optional[str] = None,
        lang: str = "auto",
        text_direction: str = "horizontal",
        vertical_lang: str = "ch",
        page_range: str = "1-5, -3",
    ) -> Optional[Dict]:
        """Extract citation from PDF with enhanced mixed layout processing."""
        temp_pdf_path = None
        searchable_pdf_path = None
        
        try:
            print(f"📄 Starting PDF citation extraction...")

            # Step 1: Analyze original PDF for page count
            print("🔍 Step 1: Analyzing original PDF structure...")
            num_pages, _ = self._analyze_pdf_structure(input_pdf_path)
            if num_pages == 0:
                logging.error(f"Could not read PDF file: {input_pdf_path}")
                return None

            # Step 2: Document Type Pre-filtering by Page Count
            print(f"📊 Step 2: Document type pre-filtering from page count ({num_pages} pages)...")
            if num_pages >= 70:
                allowed_doc_types = ["book", "thesis"]
                page_count_hint = "book"  # Default preference
                print(f"📋 Page count ≥70: Will choose between BOOK or THESIS")
            else:
                allowed_doc_types = ["journal", "bookchapter"]  
                page_count_hint = "journal"  # Default preference
                print(f"📋 Page count <70: Will choose between JOURNAL or BOOKCHAPTER")

            # Step 3: Create subset PDF from page range
            print(f"✂️ Step 3: Creating temporary PDF from page range '{page_range}'...")
            temp_pdf_path = create_subset_pdf(input_pdf_path, page_range, num_pages)
            if not temp_pdf_path:
                return None

            accumulated_text = ""
            doc_type = doc_type_override

            # Step 4: Branch on text direction mode
            if text_direction == "horizontal":
                print("📋 Step 4: Processing in HORIZONTAL mode...")
                accumulated_text = self._process_horizontal_mode(temp_pdf_path)
                
            elif text_direction == "vertical":
                print("📋 Step 4: Processing in VERTICAL mode...")
                self._used_vertical_mode = True
                accumulated_text = self._process_vertical_mode(temp_pdf_path)
                
            elif text_direction == "auto":
                print("📋 Step 4: Processing in AUTO mode (first page analysis)...")
                accumulated_text = self._process_auto_mode(temp_pdf_path)
            
            if not accumulated_text.strip():
                print("❌ No text could be extracted from PDF.")
                return None

            # Step 5: Document Type Determination with Pre-filtering
            print("🔍 Step 5: Determining document type with pre-filtering...")
            if not doc_type:
                doc_type = self._determine_document_type_filtered(temp_pdf_path, num_pages, allowed_doc_types, page_count_hint)
                print(f"📋 Determined document type: {doc_type.upper()}")

            # Steps 6-8: Keep unchanged (page numbers, LLM extraction, save)
            citation_info = {}
            if doc_type in ["journal", "bookchapter"]:
                print(f"🤖 Step 6: Specialized page number extraction for {doc_type}...")
                # Use searchable PDF if available, otherwise temp PDF
                pdf_for_analysis = searchable_pdf_path if searchable_pdf_path else temp_pdf_path
                page_number_info = self.llm.extract_page_numbers_for_journal_chapter(
                    pdf_for_analysis, page_range
                )
                if "page_numbers" in page_number_info:
                    citation_info["page_numbers"] = page_number_info["page_numbers"]
                    print(f"📄 Page numbers: {citation_info['page_numbers']}")

            # Step 7: LLM Extraction
            print(f"🤖 Step 7: Extracting citation from accumulated text with LLM...")
            # Use Vertical LLM for vertical modes, regular LLM for horizontal
            if text_direction in ["vertical", "auto"] and hasattr(self, "_used_vertical_mode"):
                vertical_llm = VerticalCitationLLM()
                extracted_info = vertical_llm.extract_vertical_citation(accumulated_text, doc_type)
                print("📋 Using Vertical Citation LLM for Traditional Chinese/Japanese text")
            else:
                extracted_info = self.llm.extract_citation_from_text(accumulated_text, doc_type)
                print("📋 Using Regular Citation LLM")
            
            citation_info.update(extracted_info)

            if not citation_info:
                print("❌ Failed to extract any citation information with LLM.")
                return None

            # Step 8: Convert to CSL JSON and save
            print("💾 Step 8: Converting to CSL JSON and saving...")
            csl_data = to_csl_json(citation_info, doc_type)
            save_citation(csl_data, output_dir)
            print("✅ Citation extraction completed successfully!")
            return csl_data

        except Exception as e:
            logging.error(f"Error extracting citation from PDF: {e}")
            import traceback
            logging.debug(traceback.format_exc())
            return None
        finally:
            # Clean up temporary files
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
                logging.info(f"Removed temporary file: {temp_pdf_path}")
            if searchable_pdf_path and searchable_pdf_path != temp_pdf_path and os.path.exists(searchable_pdf_path):
                if "temp" in searchable_pdf_path.lower() or "tmp" in os.path.basename(searchable_pdf_path):
                    os.remove(searchable_pdf_path)
                    logging.info(f"Removed temporary OCR file: {searchable_pdf_path}")

    def _process_vertical_mode(self, temp_pdf_path: str) -> str:
        """Process subset PDF in vertical mode with per-page analysis and mixed processing."""
        print("🔍 Vertical mode: Per-page analysis and mixed processing...")
        
        doc = fitz.open(temp_pdf_path)
        page_classifications = []
        accumulated_text = ""
        
        # Analyze each page for layout (same as current auto mode)
        for page_num in range(doc.page_count):
            page = doc[page_num]
            pix = page.get_pixmap()
            
            # Skip blank pages
            if self._is_page_blank_simple(pix):
                print(f"📄 Page {page_num + 1}: Blank, skipping...")
                page_classifications.append("blank")
                continue
            
            # Determine if page is vertical or horizontal
            try:
                from .vertical_handler import is_vertical_from_layout
                is_vertical = is_vertical_from_layout(pix, "ch")
                layout_type = "vertical" if is_vertical else "horizontal"
                page_classifications.append(layout_type)
                print(f"📄 Page {page_num + 1}: {layout_type}")
            except Exception as e:
                print(f"⚠️ Page {page_num + 1}: Layout detection failed ({e}), assuming vertical")
                page_classifications.append("vertical")  # Default to vertical in vertical mode
        
        doc.close()
        
        # Process pages based on classification
        print(f"📋 Processing {len(page_classifications)} pages with vertical-oriented mixed strategy...")
        
        doc = fitz.open(temp_pdf_path)
        for page_num, layout_type in enumerate(page_classifications):
            if layout_type == "blank":
                continue
                
            try:
                if layout_type == "vertical":
                    print(f"🔤 Page {page_num + 1}: Processing with PaddleOCR (vertical)...")
                    page_text = self._extract_vertical_page_text(doc, page_num)
                else:  # horizontal pages in vertical mode
                    print(f"🔤 Page {page_num + 1}: Processing with Vertical OCR (horizontal page in vertical doc)...")
                    page_text = self._extract_horizontal_page_with_vertical_ocr(doc, page_num)
                
                if page_text.strip():
                    accumulated_text += page_text + "\n\n---\n\n"
                else:
                    print(f"⚠️ Page {page_num + 1}: No text extracted")
                    
            except Exception as e:
                print(f"❌ Page {page_num + 1}: Processing failed ({e}), skipping...")
                continue
        
        doc.close()
        return accumulated_text

    def _process_auto_mode(self, temp_pdf_path: str) -> str:
        """Process subset PDF in auto mode - analyze first page only and switch mode."""
        print("🔍 Auto mode: Analyzing first page to determine mode...")
        
        doc = fitz.open(temp_pdf_path)
        if doc.page_count == 0:
            doc.close()
            return ""
        
        # Analyze only the first page
        first_page = doc[0]
        first_pix = first_page.get_pixmap()
        doc.close()
        
        # Check if first page is blank
        if self._is_page_blank_simple(first_pix):
            print("📄 First page is blank, trying next pages...")
            # Try a few more pages to find content
            doc = fitz.open(temp_pdf_path)
            for page_num in range(1, min(3, doc.page_count)):
                page = doc[page_num]
                pix = page.get_pixmap()
                if not self._is_page_blank_simple(pix):
                    first_pix = pix
                # Check if this page is a cover page
                if self.is_cover_page(page):
                    print(f"📄 Page {page_num + 1} is a cover page, trying next...")
                    continue
                    print(f"📄 Using page {page_num + 1} for layout analysis")
                    break
            doc.close()
        
        # Determine layout of first content page
        try:
            from .vertical_handler import is_vertical_from_layout
            first_page_is_vertical = is_vertical_from_layout(first_pix, "ch")
            
            if first_page_is_vertical:
                print("📋 First page is VERTICAL → Switching to VERTICAL mode")
                self._used_vertical_mode = True
                return self._process_vertical_mode(temp_pdf_path)
            else:
                print("📋 First page is HORIZONTAL → Switching to HORIZONTAL mode")
                return self._process_horizontal_mode(temp_pdf_path)
                
        except Exception as e:
            print(f"⚠️ First page layout detection failed ({e}) → Defaulting to HORIZONTAL mode")
            return self._process_horizontal_mode(temp_pdf_path)

    def _extract_horizontal_page_with_vertical_ocr(self, doc, page_num: int) -> str:
        """Extract text from a horizontal page using vertical OCR languages."""
        try:
            # Create single page temp file
            temp_single_page = f"/tmp/single_horizontal_vertical_ocr_{page_num}.pdf"
            single_doc = fitz.open()
            single_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            single_doc.save(temp_single_page)
            single_doc.close()
            
            # Check if already has text
            test_doc = fitz.open(temp_single_page)
            existing_text = test_doc[0].get_text().strip()
            test_doc.close()
            
            if existing_text:
                page_text = existing_text
            else:
                # Use vertical OCR languages for consistency in vertical mode
                from .ocr_lang_detect import get_vertical_ocr_languages
                from .utils import ensure_searchable_pdf
                
                ocr_lang = get_vertical_ocr_languages()  # chi_tra_vert+jpn_vert
                ocr_page_path = ensure_searchable_pdf(temp_single_page, ocr_lang)
                
                # Extract text
                ocr_doc = fitz.open(ocr_page_path)
                page_text = ocr_doc[0].get_text()
                ocr_doc.close()
                
                # Cleanup OCR file if different
                if ocr_page_path != temp_single_page and os.path.exists(ocr_page_path):
                    os.remove(ocr_page_path)
            
            # Cleanup
            os.remove(temp_single_page)
            return page_text or ""
            
        except Exception as e:
            print(f"❌ Vertical OCR failed for horizontal page {page_num + 1}: {e}")
            return ""

    def _determine_document_type_filtered(self, temp_pdf_path: str, num_pages: int, allowed_types: list, default_type: str) -> str:
        """Determine document type with pre-filtering based on page count."""
        try:
            # Use existing document type detection
            detected_type = determine_document_type(temp_pdf_path, num_pages)
            
            # Check if detected type is in allowed types
            if detected_type in allowed_types:
                print(f"📋 Detected type '{detected_type}' is allowed by page count filter")
                return detected_type
            else:
                print(f"📋 Detected type '{detected_type}' not allowed by page count filter, using default '{default_type}'")
                return default_type
                
        except Exception as e:
            print(f"⚠️ Document type detection failed ({e}), using default '{default_type}'")
            return default_type
    def _analyze_pdf_structure(self, pdf_path: str) -> tuple:
        """Analyze PDF structure using PyMuPDF."""
        try:
            doc = fitz.open(pdf_path)
            num_pages = doc.page_count
            filename = os.path.basename(pdf_path)

            # Extract basic metadata
            metadata = doc.metadata
            logging.info(f"PDF metadata: {metadata}")

            doc.close()
            return num_pages, filename
        except Exception as e:
            logging.error(f"Error analyzing PDF structure: {e}")
            return 0, ""


    def _process_horizontal_mode(self, temp_pdf_path: str) -> str:
        """Process subset PDF in horizontal mode (temp_pdf_path contains only page-range pages)."""
        print("🔍 Horizontal mode: Checking if PDF is searchable...")
        
        # Check if already searchable
        doc = fitz.open(temp_pdf_path)
        has_text = False
        for i in range(min(3, doc.page_count)):
            if doc[i].get_text().strip():
                has_text = True
                break
        doc.close()
        
        if has_text:
            print("📄 PDF is already searchable.")
            searchable_pdf_path = temp_pdf_path
        else:
            print("🔍 PDF is scanned, performing enhanced language detection...")
            from .utils import ensure_searchable_pdf_with_detection
            searchable_pdf_path = ensure_searchable_pdf_with_detection(temp_pdf_path)
        
        # Extract text from subset pages
        print("📄 Extracting text from subset pages...")
        # Skip cover pages during text extraction
        non_cover_pages = []
        for i in non_cover_pages:
            page = doc[i]
            if self.is_cover_page(page):
                print(f"📄 Page {i + 1}: Cover page detected, skipping...")
                continue
            non_cover_pages.append(i)
        
        if not non_cover_pages:
            print("⚠️ All pages detected as cover pages, processing anyway...")
            non_cover_pages = list(range(doc.page_count))
        accumulated_text = ""
        doc = fitz.open(searchable_pdf_path)
        for i in non_cover_pages:
            page_text = extract_pdf_text(searchable_pdf_path, page_number=i)
            if page_text.strip():
                accumulated_text += page_text + "\n\n"
        doc.close()
        
        return accumulated_text

    def _is_page_blank_simple(self, pix) -> bool:
        """Simple check if page is mostly blank."""
        import numpy as np
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, -1)
        
        if img_array.shape[2] > 1:
            gray_img = np.mean(img_array, axis=2)
        else:
            gray_img = img_array.squeeze()

        non_white_pixels = np.sum(gray_img < 250)
        total_pixels = pix.width * pix.height
        non_white_percentage = (non_white_pixels / total_pixels) * 100
        
        return non_white_percentage < 1.0

    def _extract_vertical_page_text(self, doc, page_num: int) -> str:
        """Extract text from a vertical page using PaddleOCR."""
        try:
            # Create single page temp file
            temp_single_page = f"/tmp/single_vertical_page_{page_num}.pdf"
            single_doc = fitz.open()
            single_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            single_doc.save(temp_single_page)
            single_doc.close()
            
            # Use PaddleOCR
            from .vertical_handler import process_vertical_pdf
            page_text = process_vertical_pdf(temp_single_page, "ch", page_limit=1)
            
            # Cleanup
            os.remove(temp_single_page)
            return page_text or ""
            
        except Exception as e:
            print(f"❌ PaddleOCR failed for page {page_num + 1}: {e}")
            return ""

    def _extract_horizontal_page_text(self, doc, page_num: int) -> str:
        """Extract text from a horizontal page using Tesseract."""
        try:
            # Create single page temp file
            temp_single_page = f"/tmp/single_horizontal_page_{page_num}.pdf"
            single_doc = fitz.open()
            single_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            single_doc.save(temp_single_page)
            single_doc.close()
            
            # Check if already has text
            test_doc = fitz.open(temp_single_page)
            existing_text = test_doc[0].get_text().strip()
            test_doc.close()
            
            if existing_text:
                page_text = existing_text
            else:
                # Use Tesseract with Traditional Chinese + Japanese
                from .ocr_lang_detect import get_auto_mode_horizontal_ocr_languages
                from .utils import ensure_searchable_pdf
                
                ocr_lang = get_auto_mode_horizontal_ocr_languages()
                ocr_page_path = ensure_searchable_pdf(temp_single_page, ocr_lang)
                
                # Extract text
                ocr_doc = fitz.open(ocr_page_path)
                page_text = ocr_doc[0].get_text()
                ocr_doc.close()
                
                # Cleanup OCR file if different
                if ocr_page_path != temp_single_page and os.path.exists(ocr_page_path):
                    os.remove(ocr_page_path)
            
            # Cleanup
            os.remove(temp_single_page)
            return page_text or ""
            
        except Exception as e:
            print(f"❌ Tesseract failed for page {page_num + 1}: {e}")
            return ""

    def is_cover_page(self, page) -> bool:
        """Detect cover page based on text-to-image ratio analysis"""
        try:
            # Get text and image blocks
            text_blocks = page.get_text("dict")["blocks"]
            image_blocks = page.get_images()
            
            # Calculate text area
            text_area = 0
            for block in text_blocks:
                if "lines" in block:  # Text block
                    bbox = block["bbox"]
                    text_area += (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            
            # Calculate image area
            image_area = 0
            for img in image_blocks:
                # Each image is (xref, smask, width, height, bpc, colorspace, alt, name, filter)
                if len(img) >= 4:
                    image_area += img[2] * img[3]  # width * height
            
            # If images dominate (>2.3 times text area), likely a cover page
            return image_area > text_area * 2.3
            
        except Exception as e:
            print(f"⚠️ Cover page detection failed: {e}")
            return False  # If detection fails, assume it's content
