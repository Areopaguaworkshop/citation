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
        lang: str = "eng+chi_sim",
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
                    input_source, output_dir, doc_type_override, lang, page_range
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
        lang: str = "eng+chi_sim",
        page_range: str = "1-5, -3",
    ) -> Optional[Dict]:
        """Extract citation from PDF using the new efficient, iterative workflow."""
        temp_pdf_path = None
        try:
            print(f"📄 Starting PDF citation extraction...")

            # Step 1: Analyze original PDF for page count
            print("🔍 Step 1: Analyzing original PDF structure...")
            num_pages, _ = self._analyze_pdf_structure(input_pdf_path)
            if num_pages == 0:
                logging.error(f"Could not read PDF file: {input_pdf_path}")
                return None

            # Step 2: Create a temporary subset PDF based on page_range
            print(f"✂️ Step 2: Creating temporary PDF from page range '{page_range}'...")
            temp_pdf_path = create_subset_pdf(input_pdf_path, page_range, num_pages)
            if not temp_pdf_path:
                return None # Error handled in create_subset_pdf

            # Step 3: Ensure the temporary PDF is searchable (OCR if needed)
            print("🔍 Step 3: Ensuring temporary PDF is searchable...")
            searchable_pdf_path = ensure_searchable_pdf(temp_pdf_path, lang)

            # Step 4: Determine document type
            print("🔍 Step 4: Determining document type...")
            doc = fitz.open(searchable_pdf_path)
            temp_num_pages = doc.page_count
            doc.close()

            if doc_type_override:
                doc_type = doc_type_override
                print(f"📋 Document type overridden to: {doc_type}")
            else:
                doc_type = determine_document_type(searchable_pdf_path, num_pages)
                print(f"📋 Determined document type: {doc_type.upper()}")

            citation_info = {}

            # Step 5: Specialized page number extraction for journals and book chapters
            if doc_type in ["journal", "bookchapter"]:
                print(f"🤖 Step 5: Specialized page number extraction for {doc_type}...")
                doc = fitz.open(searchable_pdf_path)
                if doc.page_count > 0:
                    # Use improved pattern-based page extraction
                    page_number_info = self.llm.extract_page_numbers_for_journal_chapter(
                        searchable_pdf_path, page_range
                    )
                    if "page_numbers" in page_number_info:
                        citation_info["page_numbers"] = page_number_info["page_numbers"]
                        print(f"📄 Page numbers extracted by improved method: {citation_info['page_numbers']}")
                doc.close()




            # Step 6: Iterative LLM Extraction for all other fields
            print(f"🤖 Step 6: Starting iterative LLM extraction for {doc_type}...")
            accumulated_text = ""

            doc = fitz.open(searchable_pdf_path)
            for i in range(doc.page_count):
                print(f"  - Processing page {i + 1} of {doc.page_count}...")
                page_text = extract_pdf_text(searchable_pdf_path, page_number=i)
                accumulated_text += page_text + "\n\n"

                # Call LLM with the accumulated text
                current_citation = self.llm.extract_citation_from_text(accumulated_text, doc_type)

                # Merge new findings into our main citation_info
                for key, value in current_citation.items():
                    if key not in citation_info:
                        citation_info[key] = value

                # Check for early exit
                if _has_all_essential_fields(citation_info, doc_type):
                    print(f"✅ All essential fields for '{doc_type}' found. Stopping early.")
                    break
            doc.close()

            # Note: Online search step has been removed
            if not _has_all_essential_fields(citation_info, doc_type):
                print(f"⚠️ Some essential fields for '{doc_type}' may be missing, but proceeding with available data.")

            if not citation_info:
                print("❌ Failed to extract any citation information with LLM.")
                return None

            # Step 7: Convert to CSL JSON and save
            print("💾 Step 7: Converting to CSL JSON and saving...")
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
            # Clean up the temporary file
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
                logging.info(f"Removed temporary file: {temp_pdf_path}")
            # If OCR created a file from a temp file, clean that up too
            if 'searchable_pdf_path' in locals() and searchable_pdf_path != temp_pdf_path and os.path.exists(searchable_pdf_path):
                 if "temp" in searchable_pdf_path.lower() or "tmp" in os.path.basename(searchable_pdf_path):
                    os.remove(searchable_pdf_path)
                    logging.info(f"Removed temporary OCR file: {searchable_pdf_path}")



    def extract_from_media_file(
        self, input_media_path: str, output_dir: str = "example"
    ) -> Optional[Dict]:
        """Extract citation from a local video/audio file."""
        try:
            print(f"📹 Starting media file citation extraction...")
            media_info = MediaInfo.parse(input_media_path)
            citation_info = {}

            # Extract metadata from the general track
            general_track = media_info.tracks[0]

            # Title
            title = getattr(general_track, "title", None)
            if title:
                citation_info["title"] = title
            else:
                # Fallback to filename
                base_name = os.path.splitext(os.path.basename(input_media_path))[0]
                citation_info["title"] = base_name.replace("_", " ").replace("-", " ")

            # Author/Performer
            author = getattr(general_track, "performer", None) or getattr(
                general_track, "artist", None
            )
            if author:
                citation_info["author"] = author

            # Year
            year = getattr(general_track, "recorded_date", None)
            if year:
                citation_info["year"] = str(year)

            # Publisher
            publisher = getattr(general_track, "publisher", None)
            if publisher:
                citation_info["publisher"] = publisher

            # Duration
            duration_ms = getattr(general_track, "duration", 0)
            if duration_ms:
                duration_s = int(duration_ms) // 1000
                minutes = duration_s // 60
                seconds = duration_s % 60
                citation_info["duration"] = f"{minutes} min., {seconds} sec."

            # Determine media type for CSL
            media_type = "audio" if general_track.track_type == "Audio" else "video"

            # Save citation
            csl_data = to_csl_json(citation_info, media_type)
            save_citation(csl_data, output_dir)
            print("✅ Media citation extraction completed successfully!")
            return csl_data

        except Exception as e:
            logging.error(f"Error extracting citation from media file: {e}")
            return None

    def extract_from_url(self, url: str, output_dir: str = "example") -> Optional[Dict]:
        """Extract citation from URL."""
        try:
            print(f"🌐 Starting URL citation extraction...")

            # Step 1: Determine URL type
            print("🔍 Step 1: Determining URL type...")
            url_type = determine_url_type(url)
            print(f"📋 URL type: {url_type}")

            # Step 2: Extract content based on URL type
            if url_type == "text":
                print("🔍 Step 2: Extracting from text-based URL...")
                citation_info = self._extract_from_text_url(url)
            else:
                print("🔍 Step 2: Extracting media metadata...")
                citation_info = self._extract_media_metadata(url)

            # Step 3: Finalize and save citation
            if citation_info:
                citation_info["url"] = url
                citation_info["date_accessed"] = datetime.now().strftime("%Y-%m-%d")

                csl_type = "webpage" if url_type == "text" else "video"

                print("💾 Step 4: Converting to CSL JSON and saving...")
                csl_data = to_csl_json(citation_info, csl_type)
                save_citation(csl_data, output_dir)

                print("✅ URL citation extraction completed successfully!")
                return csl_data
            else:
                print("❌ Failed to extract citation from URL")
                return None

        except Exception as e:
            logging.error(f"Error extracting citation from URL: {e}")
            return None

    def _extract_from_text_url(self, url: str) -> Dict:
        """Extracts citation from a text-based URL, using crawl4ai as a fallback."""
        citation_info = {}
        essential_fields = ["title", "author", "date", "container-title"]

        # Step 1: Initial extraction with Trafilatura
        try:
            print("🔍 Step 1: Extracting with trafilatura...")
            cleaned_url = clean_url(url)
            downloaded = trafilatura.fetch_url(cleaned_url)
            if downloaded:
                metadata = trafilatura.extract_metadata(downloaded)
                if metadata:
                    if metadata.title:
                        citation_info["title"] = metadata.title
                    if metadata.author:
                        citation_info["author"] = metadata.author
                    if metadata.date:
                        citation_info["date"] = metadata.date
                    if metadata.sitename:
                        citation_info["container-title"] = metadata.sitename
                    print(f"📝 Trafilatura extraction: {len(citation_info)} fields found")
        except Exception as e:
            logging.warning(f"Trafilatura failed: {e}")

        # Step 2: Check for missing fields and use crawl4ai if necessary
        missing_fields = [field for field in essential_fields if field not in citation_info]
        if missing_fields:
            print(f"⚠️ Missing essential fields: {', '.join(missing_fields)}. Using crawl4ai as fallback...")
            try:
                markdown_content = asyncio.run(self._extract_with_crawl4ai(url))
                if markdown_content:
                    print("🤖 Step 2a: Extracting missing info with LLM from crawled content...")
                    llm_extracted_info = self.llm.extract_citation_from_web_markdown(markdown_content)
                    
                    # Merge missing fields
                    for field in missing_fields:
                        if field in llm_extracted_info and field not in citation_info:
                            citation_info[field] = llm_extracted_info[field]
                            print(f"✅ Found missing '{field}' with crawl4ai+LLM.")
                else:
                    print("❌ crawl4ai did not return any content.")
            except Exception as e:
                logging.error(f"crawl4ai fallback failed: {e}")

        # Step 3: Final check and logging
        final_missing = [field for field in essential_fields if field not in citation_info]
        if final_missing:
            logging.warning(f"Could not extract the following fields: {', '.join(final_missing)}")
        
        # Step 4: Extract container-title from domain if not provided
        if "container-title" not in citation_info:
            domain_publisher = extract_publisher_from_domain(url)
            if domain_publisher:
                citation_info["container-title"] = domain_publisher
                print(f"🏢 container-title derived from domain: {domain_publisher}")

        return citation_info

    async def _extract_with_crawl4ai(self, url: str) -> str:
        """Crawls a single URL using crawl4ai and returns its markdown content."""
        print("🕷️ Running crawl4ai...")
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            return result.markdown if result else ""

    def _extract_media_metadata(self, url: str) -> Dict:
        """Extract metadata from media URLs (placeholder for future implementation)."""
        try:
            # For now, return basic URL info
            # Future implementation could use youtube-dl or similar
            return {
                "title": "Media content from URL",
                "author": "Unknown",
                "container-title": extract_publisher_from_domain(url),
            }
        except Exception as e:
            logging.error(f"Error extracting media metadata: {e}")
            return {}

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

