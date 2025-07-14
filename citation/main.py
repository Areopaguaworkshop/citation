import trafilatura
from newspaper import Article
import os
import subprocess
import logging
import trafilatura
from newspaper import Article
import json
import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, Optional
import tempfile
from pymediainfo import MediaInfo

from .utils import (
    clean_url,
    format_author_name,
    extract_publisher_from_domain,
    is_url,
    is_pdf_file,
    is_media_file,
    determine_document_type,
    ensure_searchable_pdf,
    extract_pdf_text,
    determine_url_type,
    has_required_info,
    save_citation,
    guess_title_from_filename,
    detect_page_numbers,
    clean_url,
    format_author_name,
    extract_publisher_from_domain,
)
from .model import CitationLLM

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Try to import scholarly
try:
    from scholarly._scholarly import search_pubs

    print(f"scholarly object: {scholarly}")
    print(f"scholarly file: {scholarly.__file__}")
    SCHOLARLY_AVAILABLE = True
except ImportError:
    SCHOLARLY_AVAILABLE = False
    logging.warning("scholarly not available, skipping Google Scholar search")


class CitationExtractor:
    def __init__(self, llm_model="ollama/qwen3"):
        """Initialize the citation extractor."""
        self.llm = CitationLLM(llm_model)

    def extract_citation(
        self,
        input_source: str,
        output_dir: str = "citations",
        doc_type_override: Optional[str] = None,
    ) -> Optional[Dict]:
        """Main function to extract citation from either PDF or URL."""
        try:
            # Auto-detect input type
            if is_url(input_source):
                return self.extract_from_url(input_source, output_dir)
            elif is_pdf_file(input_source):
                return self.extract_from_pdf(
                    input_source, output_dir, doc_type_override
                )
            elif is_media_file(input_source):
                return self.extract_from_media_file(input_source, output_dir)
            else:
                logging.error(f"Unknown input type: {input_source}")
                return None
        except Exception as e:
            logging.error(f"Error in citation extraction: {e}")
            return None

    def extract_from_pdf(
        self,
        input_pdf_path: str,
        output_dir: str = "citations",
        doc_type_override: Optional[str] = None,
    ) -> Optional[Dict]:
        """Extract citation from PDF following the workflow."""
        try:
            print(f"📄 Starting PDF citation extraction...")

            # Step 1: Check PDF page count and determine document type
            print("🔍 Step 1: Analyzing PDF structure...")
            num_pages, filename = self._analyze_pdf_structure(input_pdf_path)

            # Determine document type (with override if provided)
            if doc_type_override:
                doc_type = doc_type_override
                print(f"📋 Document type overridden to: {doc_type}")
            else:
                doc_type = determine_document_type(num_pages)
                print(
                    f"📋 Document type determined by page count: {
                        doc_type} ({num_pages} pages)"
                )

            # Step 2: Try PyMuPDF for metadata extraction
            print("🔍 Step 2: Extracting metadata with PyMuPDF...")
            citation_info = self._extract_with_pymupdf(
                input_pdf_path, filename)

            # Step 3: Try scholarly search if we have title
            title_found = citation_info and citation_info.get("title")
            if title_found:
                print(f"✅ Title found: '{citation_info['title']}'")
                print("🔍 Step 3: Searching Google Scholar...")
                scholarly_info = self._search_with_scholarly(
                    citation_info["title"])
                if scholarly_info:
                    citation_info.update(scholarly_info)
            else:
                print(
                    "⚠️ No title found in metadata or filename, skipping Google Scholar search"
                )

            # Step 4: Check if we have enough required info
            if not has_required_info(citation_info, doc_type):
                print(
                    "🔍 Step 4: Insufficient metadata found, proceeding with OCR and LLM extraction..."
                )

                # OCR if needed
                searchable_pdf = ensure_searchable_pdf(
                    input_pdf_path, num_pages)

                # LLM extraction
                pdf_text = extract_pdf_text(searchable_pdf, doc_type)
                if pdf_text:
                    print(f"🤖 Step 5: Using LLM to extract {
                          doc_type} citation...")
                    llm_citation = self.llm.extract_citation_from_text(
                        pdf_text, doc_type
                    )

                    # Add page numbers for journal and bookchapter
                    if doc_type in ["journal", "bookchapter"] and llm_citation:
                        first_page, last_page = (
                            detect_page_numbers,
                            clean_url,
                            format_author_name,
                            extract_publisher_from_domain(searchable_pdf),
                        )
                        if first_page and last_page:
                            llm_citation["page_numbers"] = f"{
                                first_page}-{last_page}"
                            print(f"📄 Page numbers detected: {
                                  first_page}-{last_page}")

                    if llm_citation:
                        citation_info.update(llm_citation)
            else:
                print("✅ Sufficient metadata found, skipping OCR and LLM extraction")

            if citation_info:
                # Step 6: Save output
                print("💾 Step 6: Saving citation files...")
                save_citation(citation_info, input_pdf_path, output_dir)
                print("✅ Citation extraction completed successfully!")
                return citation_info
            else:
                print("❌ Failed to extract citation information")
                return None

        except Exception as e:
            logging.error(f"Error extracting citation from PDF: {e}")
            return None

    def extract_from_media_file(
        self, input_media_path: str, output_dir: str = "citations"
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
                base_name = os.path.splitext(
                    os.path.basename(input_media_path))[0]
                citation_info["title"] = base_name.replace(
                    "_", " ").replace("-", " ")

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

            # Save citation
            save_citation(citation_info, input_media_path, output_dir)
            print("✅ Media citation extraction completed successfully!")
            return citation_info

        except Exception as e:
            logging.error(f"Error extracting citation from media file: {e}")
            return None

    def extract_from_url(
        self, url: str, output_dir: str = "citations"
    ) -> Optional[Dict]:
        """Extract citation from URL."""
        try:
            print(f"🌐 Starting URL citation extraction...")

            # Step 1: Determine URL type
            print("🔍 Step 1: Determining URL type...")
            url_type = determine_url_type(url)
            print(f"📋 URL type: {url_type}")

            # Step 2: Extract using anystyle for text-based content
            if url_type == "text":
                print("🔍 Step 2: Extracting with trafilatura...")
                citation_info = self._extract_url_with_trafilatura(url)
            else:
                # Step 3: Extract metadata for video/audio
                print("🔍 Step 2: Extracting media metadata...")
                citation_info = self._extract_media_metadata(url)

            if citation_info:
                citation_info["url"] = url
                citation_info["date_accessed"] = datetime.now().strftime(
                    "%Y-%m-%d")
                print("💾 Step 3: Saving citation files...")
                save_citation(citation_info, url, output_dir)
                print("✅ URL citation extraction completed successfully!")
                return citation_info
            else:
                print("❌ Failed to extract citation from URL")
                return None

        except Exception as e:
            logging.error(f"Error extracting citation from URL: {e}")
            return None

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

    def _extract_with_pymupdf(self, pdf_path: str, filename: str) -> Dict:
        """Extract metadata using PyMuPDF."""
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            doc.close()

            citation_info = {}

            # Extract title from metadata
            title = metadata.get("title", "").strip()
            if title:
                citation_info["title"] = title
                print(f"📋 Title found in metadata: '{title}'")
            else:
                # Try to guess title from filename
                guessed_title = guess_title_from_filename(filename)
                if guessed_title:
                    citation_info["title"] = guessed_title
                    print(f"📋 Title guessed from filename: '{guessed_title}'")
                else:
                    print("⚠️ No title found in metadata or filename")

            # Extract author from metadata
            author = metadata.get("author", "").strip()
            if author:
                citation_info["author"] = author
                print(f"👤 Author found in metadata: '{author}'")

            # Extract other metadata
            subject = metadata.get("subject", "").strip()
            if subject:
                citation_info["subject"] = subject

            creator = metadata.get("creator", "").strip()
            if creator and creator != author:
                citation_info["creator"] = creator

            # Extract creation date
            creation_date = metadata.get("creationDate", "").strip()
            if creation_date:
                # Try to extract year from creation date
                import re

                year_match = re.search(r"(\d{4})", creation_date)
                if year_match:
                    citation_info["year"] = year_match.group(1)
                    print(
                        f"📅 Year extracted from creation date: {
                            year_match.group(1)}"
                    )

            logging.info(f"PyMuPDF metadata: {citation_info}")
            return citation_info

        except Exception as e:
            logging.error(f"Error with PyMuPDF: {e}")
            return {}

    def _search_with_scholarly(self, title: str) -> Dict:
        """Search Google Scholar using scholarly library."""
        if not SCHOLARLY_AVAILABLE:
            print("⚠️ Scholarly library not available, skipping Google Scholar search")
            return {}

        try:
            # Search for the publication
            search_query = scholarly.search_pubs(title)
            pub = next(search_query, None)

            if pub:
                # Fill in publication details
                filled_pub = scholarly.fill(pub)

                # Extract relevant information
                info = {}
                if "title" in filled_pub:
                    info["title"] = filled_pub["title"]
                if "author" in filled_pub:
                    authors = [author["name"]
                               for author in filled_pub["author"]]
                    info["author"] = ", ".join(authors)
                if "year" in filled_pub:
                    info["year"] = str(filled_pub["year"])
                if "venue" in filled_pub:
                    info["journal_name"] = filled_pub["venue"]
                if "publisher" in filled_pub:
                    info["publisher"] = filled_pub["publisher"]

                print(f"📚 Found additional info from Google Scholar")
                logging.info(f"Scholarly info: {info}")
                return info
            else:
                print("⚠️ No results found in Google Scholar")
                return {}
        except Exception as e:
            logging.error(f"Error with scholarly search: {e}")
            return {}

    def _extract_url_with_trafilatura(self, url: str) -> Dict:
        """Extract citation from URL using trafilatura and newspaper3k."""
        try:
            # Clean the URL
            cleaned_url = clean_url(url)
            print(f"🔧 URL cleaned: {cleaned_url}")

            citation_info = {}

            # Step 1: Try trafilatura
            print("🔍 Step 1: Extracting with trafilatura...")
            downloaded = trafilatura.fetch_url(cleaned_url)
            if downloaded:
                metadata = trafilatura.extract_metadata(downloaded)
                if metadata:
                    if metadata.title:
                        citation_info["title"] = metadata.title
                    if metadata.author:
                        citation_info["author"] = format_author_name(
                            metadata.author)
                    if metadata.date:
                        citation_info["date"] = metadata.date
                    if metadata.sitename:
                        citation_info["publisher"] = metadata.sitename

                    print(
                        f"📝 Trafilatura extraction: {
                            len(citation_info)} fields found"
                    )
                    logging.info(f"Trafilatura metadata: {citation_info}")

            # Step 2: Fallback to newspaper3k if needed
            if not citation_info.get("title") or not citation_info.get("author"):
                print("🔍 Step 2: Trying newspaper3k as fallback...")
                try:
                    article = Article(cleaned_url)
                    article.download()
                    article.parse()

                    if not citation_info.get("title") and article.title:
                        citation_info["title"] = article.title
                        print(f"📝 Newspaper3k extracted title: {
                              article.title}")

                    if not citation_info.get("author") and article.authors:
                        authors_str = ", ".join(article.authors)
                        citation_info["author"] = format_author_name(
                            authors_str)
                        print(f"👥 Newspaper3k extracted authors: {
                              article.authors}")

                    if not citation_info.get("date") and article.publish_date:
                        citation_info["date"] = article.publish_date.strftime(
                            "%Y-%m-%d"
                        )
                        print(f"📅 Newspaper3k extracted date: {
                              article.publish_date}")

                except Exception as e:
                    print(f"⚠️ Newspaper3k failed: {e}")
                    logging.error(f"Newspaper3k error: {e}")

            # Step 3: Fallback to HTML meta tags if still missing required fields
            if not citation_info.get("title") or not citation_info.get("author"):
                print("🔍 Step 3: Trying HTML meta tags as fallback...")
                try:
                    response = requests.get(cleaned_url, timeout=10)
                    soup = BeautifulSoup(response.content, "html.parser")

                    # Extract title from meta tags or page title
                    if not citation_info.get("title"):
                        title_tag = soup.find("title")
                        if title_tag:
                            citation_info["title"] = title_tag.get_text(
                            ).strip()
                            print(f"📝 HTML title extracted: {
                                  citation_info['title']}")

                    # Extract author from meta tags
                    if not citation_info.get("author"):
                        author_meta = soup.find(
                            "meta", attrs={"name": "author"})
                        if author_meta and author_meta.get("content"):
                            citation_info["author"] = format_author_name(
                                author_meta.get("content")
                            )
                            print(
                                f"👤 HTML meta author extracted: {
                                    citation_info['author']}"
                            )

                except Exception as e:
                    print(f"⚠️ HTML meta extraction failed: {e}")
                    logging.error(f"HTML meta extraction error: {e}")

            # Step 4: Extract publisher from domain if not provided
            if not citation_info.get("publisher"):
                domain_publisher = extract_publisher_from_domain(cleaned_url)
                if domain_publisher:
                    citation_info["publisher"] = domain_publisher
                    print(f"🏢 Publisher derived from domain: {
                          domain_publisher}")

            return citation_info

        except Exception as e:
            logging.error(f"Error with trafilatura: {e}")
            return {}


def get_pdf_citation_text(input_pdf_path, output_dir="processed_pdfs", lang="eng"):
    """Legacy function for backward compatibility."""
    extractor = CitationExtractor()
    return extractor.extract_from_pdf(input_pdf_path, output_dir)
