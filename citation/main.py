import trafilatura
from newspaper import Article
import os
import subprocess
import logging
import json
import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, Optional
import tempfile

from .utils import (
    clean_url, format_author_name, extract_publisher_from_domain,
    is_url, is_pdf_file, determine_document_type, ensure_searchable_pdf,
    extract_pdf_text, determine_url_type, has_required_info, save_citation,
    guess_title_from_filename, detect_page_numbers
)
from .model import CitationLLM

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Try to import scholarly
try:
    import scholarly
    SCHOLARLY_AVAILABLE = True
except ImportError:
    SCHOLARLY_AVAILABLE = False
    logging.warning("scholarly not available, skipping Google Scholar search")


class CitationExtractor:
    def __init__(self, llm_model="ollama/qwen3"):
        """Initialize the citation extractor."""
        self.llm = CitationLLM(llm_model)
        
    def extract_citation(self, input_source: str, output_dir: str = "citations", doc_type_override: Optional[str] = None) -> Optional[Dict]:
        """Main function to extract citation from either PDF or URL."""
        try:
            # Auto-detect input type
            if is_url(input_source):
                return self.extract_from_url(input_source, output_dir)
            elif is_pdf_file(input_source):
                return self.extract_from_pdf(input_source, output_dir, doc_type_override)
            else:
                logging.error(f"Unknown input type: {input_source}")
                return None
        except Exception as e:
            logging.error(f"Error in citation extraction: {e}")
            return None
    
    def extract_from_pdf(self, input_pdf_path: str, output_dir: str = "citations", doc_type_override: Optional[str] = None) -> Optional[Dict]:
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
                print(f"📋 Document type determined by page count: {doc_type} ({num_pages} pages)")
            
            # Step 2: Try PyMuPDF for metadata extraction
            print("🔍 Step 2: Extracting metadata with PyMuPDF...")
            citation_info = self._extract_with_pymupdf(input_pdf_path, filename)
            
            # Step 3: Try scholarly search if we have title
            title_found = citation_info and citation_info.get('title')
            if title_found:
                print(f"✅ Title found: '{citation_info['title']}'")
                print("🔍 Step 3: Searching Google Scholar...")
                scholarly_info = self._search_with_scholarly(citation_info['title'])
                if scholarly_info:
                    citation_info.update(scholarly_info)
            else:
                print("⚠️ No title found in metadata or filename, skipping Google Scholar search")
            
            # Step 4: Check if we have enough required info
            if not has_required_info(citation_info, doc_type):
                print("🔍 Step 4: Insufficient metadata found, proceeding with OCR and LLM extraction...")
                
                # OCR if needed
                searchable_pdf = ensure_searchable_pdf(input_pdf_path, num_pages)
                
                # LLM extraction
                pdf_text = extract_pdf_text(searchable_pdf, doc_type)
                if pdf_text:
                    print(f"🤖 Step 5: Using LLM to extract {doc_type} citation...")
                    llm_citation = self.llm.extract_citation_from_text(pdf_text, doc_type)
                    
                    # Add page numbers for journal and bookchapter
                    if doc_type in ["journal", "bookchapter"] and llm_citation:
                        first_page, last_page = detect_page_numbers(searchable_pdf)
                        if first_page and last_page:
                            llm_citation['page_numbers'] = f"{first_page}-{last_page}"
                            print(f"📄 Page numbers detected: {first_page}-{last_page}")
                    
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
    
    def extract_from_url(self, url: str, output_dir: str = "citations") -> Optional[Dict]:
        """Extract citation from URL."""
        try:
            print(f"🌐 Starting URL citation extraction...")
            
            # Step 1: Determine URL type
            print("🔍 Step 1: Determining URL type...")
            url_type = determine_url_type(url)
            print(f"📋 URL type: {url_type}")
            
            # Step 2: Extract using anystyle for text-based content
            if url_type == "text":
                print("🔍 Step 2: Extracting with anystyle...")
                citation_info = self._extract_url_with_anystyle(url)
            else:
                # Step 3: Extract metadata for video/audio
                print("🔍 Step 2: Extracting media metadata...")
                citation_info = self._extract_media_metadata(url)
            
            if citation_info:
                citation_info['url'] = url
                citation_info['date_accessed'] = datetime.now().strftime('%Y-%m-%d')
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
            title = metadata.get('title', '').strip()
            if title:
                citation_info['title'] = title
                print(f"📋 Title found in metadata: '{title}'")
            else:
                # Try to guess title from filename
                guessed_title = guess_title_from_filename(filename)
                if guessed_title:
                    citation_info['title'] = guessed_title
                    print(f"📋 Title guessed from filename: '{guessed_title}'")
                else:
                    print("⚠️ No title found in metadata or filename")
            
            # Extract author from metadata
            author = metadata.get('author', '').strip()
            if author:
                citation_info['author'] = author
                print(f"👤 Author found in metadata: '{author}'")
            
            # Extract other metadata
            subject = metadata.get('subject', '').strip()
            if subject:
                citation_info['subject'] = subject
            
            creator = metadata.get('creator', '').strip()
            if creator and creator != author:
                citation_info['creator'] = creator
            
            # Extract creation date
            creation_date = metadata.get('creationDate', '').strip()
            if creation_date:
                # Try to extract year from creation date
                import re
                year_match = re.search(r'(\d{4})', creation_date)
                if year_match:
                    citation_info['year'] = year_match.group(1)
                    print(f"📅 Year extracted from creation date: {year_match.group(1)}")
            
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
                if 'title' in filled_pub:
                    info['title'] = filled_pub['title']
                if 'author' in filled_pub:
                    authors = [author['name'] for author in filled_pub['author']]
                    info['author'] = ', '.join(authors)
                if 'year' in filled_pub:
                    info['year'] = str(filled_pub['year'])
                if 'venue' in filled_pub:
                    info['journal_name'] = filled_pub['venue']
                if 'publisher' in filled_pub:
                    info['publisher'] = filled_pub['publisher']
                
                print(f"📚 Found additional info from Google Scholar")
                logging.info(f"Scholarly info: {info}")
                return info
            else:
                print("⚠️ No results found in Google Scholar")
                return {}
        except Exception as e:
            logging.error(f"Error with scholarly search: {e}")
            return {}
    
    def _extract_url_with_anystyle(self, url: str) -> Dict:
        """Extract citation from URL using anystyle."""
        try:
            # First get the content from the URL
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text()
            
            # Save text to a temporary file for anystyle
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
                tmp_file.write(text_content)
                tmp_file_path = tmp_file.name
            
            try:
                # Use anystyle to parse the text
                result = subprocess.run(
                    ['anystyle', 'parse', tmp_file_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Try to parse the output as JSON
                    try:
                        citations = json.loads(result.stdout)
                        if citations:
                            # Take the first citation
                            citation = citations[0]
                            citation_info = {}
                            
                            # Map anystyle fields to our format
                            if 'title' in citation:
                                citation_info['title'] = citation['title']
                            if 'author' in citation:
                                citation_info['author'] = citation['author']
                            if 'date' in citation:
                                citation_info['date'] = citation['date']
                            if 'publisher' in citation:
                                citation_info['publisher'] = citation['publisher']
                            
                            print(f"📋 Anystyle extracted: {len(citation_info)} fields")
                            logging.info(f"Anystyle extraction: {citation_info}")
                            return citation_info
                    except json.JSONDecodeError:
                        logging.warning("Could not parse anystyle output as JSON")
                        return {}
                else:
                    logging.warning(f"Anystyle failed: {result.stderr}")
                    return {}
            finally:
                # Clean up temporary file
                os.unlink(tmp_file_path)
                
        except Exception as e:
            logging.error(f"Error with anystyle: {e}")
            return {}
    
    def _extract_media_metadata(self, url: str) -> Dict:
        """Extract metadata from media URLs."""
        try:
            # Basic web scraping for metadata
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            citation_info = {}
            
            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                citation_info['title'] = title_tag.get_text().strip()
            
            # Extract meta information
            meta_tags = soup.find_all('meta')
            for tag in meta_tags:
                name = tag.get('name', '').lower()
                content = tag.get('content', '')
                
                if name == 'author':
                    citation_info['author'] = content
                elif name == 'date':
                    citation_info['date'] = content
                elif name == 'publisher':
                    citation_info['publisher'] = content
            
            print(f"📋 Media metadata extracted: {len(citation_info)} fields")
            logging.info(f"Media metadata: {citation_info}")
            return citation_info
            
        except Exception as e:
            logging.error(f"Error extracting media metadata: {e}")
            return {}


# Legacy functions for backward compatibility
def get_pdf_citation_text(input_pdf_path, output_dir="processed_pdfs", lang="eng"):
    """Legacy function for backward compatibility."""
    extractor = CitationExtractor()
    return extractor.extract_from_pdf(input_pdf_path, output_dir)
