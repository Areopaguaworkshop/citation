import os
import subprocess
import logging
import fitz  # PyMuPDF
import requests
from urllib.parse import urlparse
from typing import Optional, Dict, Tuple
import re


def is_url(input_string: str) -> bool:
    """Check if the input string is a URL."""
    try:
        result = urlparse(input_string)
        return all([result.scheme, result.netloc])
    except:
        return False


def is_pdf_file(file_path: str) -> bool:
    """Check if the file is a PDF."""
    if not os.path.exists(file_path):
        return False

    try:
        # Try to open with PyMuPDF to verify it's a valid PDF
        doc = fitz.open(file_path)
        doc.close()
        return True
    except:
        return False


def is_media_file(file_path: str) -> bool:
    """Check if the file is a video or audio file."""
    if not os.path.exists(file_path):
        return False

    # Common video and audio extensions
    media_extensions = {
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",  # video
        ".mp3",
        ".wav",
        ".aac",
        ".ogg",
        ".flac",
        ".m4a",  # audio
    }

    _, ext = os.path.splitext(file_path)
    return ext.lower() in media_extensions


def determine_document_type(num_pages: int) -> str:
    """Determine document type based on page count."""
    if num_pages >= 70:
        return "book"
    else:
        return "journal"


def enhance_document_type_detection(pdf_path: str, initial_type: str) -> str:
    """Enhanced document type detection using content analysis."""
    if initial_type not in ["journal", "bookchapter"]:
        return initial_type
    
    try:
        doc = fitz.open(pdf_path)
        if doc.page_count == 0:
            return initial_type
        
        # Extract first page text for analysis
        first_page = doc[0]
        page_text = first_page.get_text().lower()
        
        # Get header and footer areas
        rect = first_page.rect
        header_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + rect.height * 0.15)
        footer_rect = fitz.Rect(rect.x0, rect.y1 - rect.height * 0.15, rect.x1, rect.y1)
        
        header_text = first_page.get_text(clip=header_rect).lower()
        footer_text = first_page.get_text(clip=footer_rect).lower()
        
        # Journal indicators
        journal_indicators = [
            'journal', 'vol.', 'volume', 'issue', 'no.', 'number', 
            'issn', 'proceedings', 'quarterly', 'annual', 'review',
            '期刊', '卷', '期', '号', '学报', '杂志'  # Chinese indicators
        ]
        
        # Book chapter indicators
        chapter_indicators = [
            'chapter', 'book', 'editor', 'edited by', 'isbn', 
            'publisher', 'press', 'publication',
            '章', '篇', '编', '主编', '出版社', '出版'  # Chinese indicators
        ]
        
        # Count indicators in header and footer
        journal_score = sum(1 for indicator in journal_indicators 
                          if indicator in header_text or indicator in footer_text)
        chapter_score = sum(1 for indicator in chapter_indicators 
                          if indicator in header_text or indicator in footer_text)
        
        # Also check page numbering patterns
        # Journals often have continuous page numbering
        # Book chapters often have chapter-specific numbering
        page_numbers = detect_page_numbers(pdf_path)
        if page_numbers[0] and page_numbers[0] > 100:  # High page numbers suggest journal
            journal_score += 1
        
        # Decision logic
        if journal_score > chapter_score:
            return "journal"
        elif chapter_score > journal_score:
            return "bookchapter"
        else:
            # Default to journal for short documents when unclear
            return "journal"
        
        doc.close()
        
    except Exception as e:
        logging.error(f"Error in enhanced document type detection: {e}")
        return initial_type


def guess_title_from_filename(filename: str) -> Optional[str]:
    """Guess title from PDF filename by removing common prefixes/suffixes."""
    # Remove file extension
    title = os.path.splitext(filename)[0]

    # Remove common prefixes and suffixes
    prefixes_to_remove = [
        r"^paper[_\-\s]*",
        r"^article[_\-\s]*",
        r"^document[_\-\s]*",
        r"^draft[_\-\s]*",
        r"^final[_\-\s]*",
        r"^submission[_\-\s]*",
        r"^\d{4}[_\-\s]*",  # Year prefixes
    ]

    suffixes_to_remove = [
        r"[_\-\s]*final$",
        r"[_\-\s]*draft$",
        r"[_\-\s]*v\d+$",  # Version numbers
        r"[_\-\s]*\d{4}$",  # Year suffixes
        r"[_\-\s]*revised$",
        r"[_\-\s]*submitted$",
    ]

    for prefix in prefixes_to_remove:
        title = re.sub(prefix, "", title, flags=re.IGNORECASE)

    for suffix in suffixes_to_remove:
        title = re.sub(suffix, "", title, flags=re.IGNORECASE)

    # Replace underscores and hyphens with spaces
    title = re.sub(r"[_\-]+", " ", title)

    # Clean up multiple spaces
    title = re.sub(r"\s+", " ", title).strip()

    # Only return if it seems like a reasonable title (not too short)
    if len(title) > 3:
        return title

    return None


def detect_page_numbers(pdf_path: str) -> Tuple[Optional[int], Optional[int]]:
    """Detect first and last page numbers from PDF footer."""
    try:
        doc = fitz.open(pdf_path)
        first_page_num = None
        last_page_num = None

        # Check first few pages for page number
        for page_idx in range(min(3, doc.page_count)):
            page = doc[page_idx]

            # Get text from bottom 20% of page (footer area)
            rect = page.rect
            footer_rect = fitz.Rect(
                rect.x0, rect.y1 - rect.height * 0.2, rect.x1, rect.y1
            )
            footer_text = page.get_text(clip=footer_rect)

            # Look for standalone numbers in footer
            numbers = re.findall(r"\b(\d+)\b", footer_text)
            if numbers:
                # Take the first reasonable number found
                for num_str in numbers:
                    num = int(num_str)
                    if 1 <= num <= 9999:  # Reasonable page number range
                        if first_page_num is None:
                            first_page_num = num - page_idx  # Deduce first page number
                        break
                if first_page_num is not None:
                    break

        # Check last page for page number
        if doc.page_count > 0:
            last_page = doc[doc.page_count - 1]
            rect = last_page.rect
            footer_rect = fitz.Rect(
                rect.x0, rect.y1 - rect.height * 0.2, rect.x1, rect.y1
            )
            footer_text = last_page.get_text(clip=footer_rect)

            numbers = re.findall(r"\b(\d+)\b", footer_text)
            if numbers:
                for num_str in numbers:
                    num = int(num_str)
                    if 1 <= num <= 9999:
                        last_page_num = num
                        break

        doc.close()
        return first_page_num, last_page_num

    except Exception as e:
        logging.error(f"Error detecting page numbers: {e}")
        return None, None


def ensure_searchable_pdf(pdf_path: str, num_pages: int) -> str:
    """Ensure PDF is searchable using OCR if needed."""
    try:
        # Check if PDF is already searchable
        doc = fitz.open(pdf_path)
        first_page = doc[0]
        text = first_page.get_text()
        doc.close()

        if text.strip():
            logging.info("PDF is already searchable")
            return pdf_path

        # OCR the PDF
        logging.info("PDF is not searchable, running OCR...")

        output_dir = os.path.dirname(pdf_path)
        if not output_dir:
            output_dir = "."
        ocr_output = os.path.join(
            output_dir, f"ocr_{os.path.basename(pdf_path)}")

        # Determine OCR pages based on document type
        if num_pages < 70:
            # OCR all pages for short documents
            ocr_pages = None
        else:
            # OCR first 10 and last 2 pages for long documents
            if num_pages <= 12:
                ocr_pages = None # OCR all pages if it's this short
            else:
                ocr_pages = f"1-10,{num_pages-1}-{num_pages}"

        cmd = ["ocrmypdf", "--deskew", "--force-ocr", "-l", "eng+chi_sim"]
        if ocr_pages:
            cmd.extend(["--pages", ocr_pages])
        cmd.extend([pdf_path, ocr_output])

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            logging.info(f"OCR completed successfully: {ocr_output}")
            return ocr_output
        else:
            logging.error(f"OCR failed: {result.stderr}")
            return pdf_path

    except Exception as e:
        logging.error(f"Error ensuring searchable PDF: {e}")
        return pdf_path


def extract_pdf_text(pdf_path: str, doc_type: str) -> str:
    """Extract text from PDF based on document type."""
    try:
        doc = fitz.open(pdf_path)
        text = ""

        if doc_type in ["book", "thesis"]:
            # For books/thesis, extract first 10 and last 2 pages
            pages_to_extract = list(range(min(10, doc.page_count)))
            
            if doc.page_count > 12:
                pages_to_extract.extend(range(doc.page_count - 2, doc.page_count))
            
            # Remove duplicates and sort
            pages_to_extract = sorted(list(set(pages_to_extract)))

            for i in pages_to_extract:
                page = doc[i]
                text += page.get_text() + "\n"
        else:  # journal or bookchapter
            # Extract all pages
            for page in doc:
                text += page.get_text() + "\n"

        doc.close()
        return text

    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return ""


def determine_url_type(url: str) -> str:
    """Determine URL type."""
    try:
        response = requests.head(url, timeout=10)
        content_type = response.headers.get("content-type", "").lower()

        if "video" in content_type or "audio" in content_type:
            return "media"
        else:
            return "text"
    except Exception as e:
        logging.error(f"Error determining URL type: {e}")
        return "text"


def save_citation(citation_info: Dict, input_source: str, output_dir: str):
    """Save citation information as YAML and JSON."""
    import yaml
    import json

    def sanitize_filename(name: str) -> str:
        """Sanitize a string to be a valid filename."""
        # Remove invalid characters
        sanitized = re.sub(r'[\\/*?:"<>|]', "", name)
        # Replace spaces with underscores
        sanitized = sanitized.replace(" ", "_")
        # Truncate to a reasonable length
        return sanitized[:100]

    try:
        os.makedirs(output_dir, exist_ok=True)

        # Generate base filename
        if is_url(input_source):
            title = citation_info.get("title")
            if title:
                base_name = sanitize_filename(title)
            else:
                base_name = "url_citation"
        else:
            # PDF or media file
            base_name = os.path.splitext(os.path.basename(input_source))[0]

        # Save as YAML
        yaml_path = os.path.join(output_dir, f"{base_name}.yaml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(citation_info, f, default_flow_style=False,
                      allow_unicode=True)

        # Save as JSON
        json_path = os.path.join(output_dir, f"{base_name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(citation_info, f, indent=2, ensure_ascii=False)

        logging.info(f"Citation saved to: {yaml_path} and {json_path}")

    except Exception as e:
        logging.error(f"Error saving citation: {e}")


def clean_url(url: str) -> str:
    """Clean URL by removing tracking parameters while preserving original format."""
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

    # Common tracking parameters to remove
    tracking_params = {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "dclid",
        "msclkid",
        "ref",
        "source",
        "campaign",
        "medium",
        "term",
        "content",
        "_ga",
        "_gid",
        "_gac",
        "mc_eid",
        "mc_cid",
    }

    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        # Remove tracking parameters
        cleaned_params = {
            k: v for k, v in query_params.items() if k not in tracking_params
        }

        # Reconstruct URL
        cleaned_query = urlencode(cleaned_params, doseq=True)
        cleaned_url = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                cleaned_query,
                parsed.fragment,
            )
        )

        return cleaned_url
    except Exception as e:
        logging.error(f"Error cleaning URL: {e}")
        return url


def format_author_name(author_name: str) -> str:
    """Format author name to surname-first format."""
    if not author_name or not author_name.strip():
        return author_name

    # Handle multiple authors separated by commas
    if "," in author_name and not author_name.count(",") == 1:
        # Multiple authors like "John Smith, Jane Doe"
        authors = [name.strip() for name in author_name.split(",")]
        formatted_authors = []

        for author in authors:
            if author:
                formatted_authors.append(format_single_author(author))

        return ", ".join(formatted_authors)
    else:
        return format_single_author(author_name)


def format_single_author(author_name: str) -> str:
    """Format a single author name to surname-first format."""
    author_name = author_name.strip()

    # If already in surname-first format (contains comma), return as is
    if "," in author_name:
        return author_name

    # Split by spaces and try to identify surname (usually last word)
    parts = author_name.split()
    if len(parts) >= 2:
        # Assume last part is surname, rest are forename(s)
        surname = parts[-1]
        forenames = " ".join(parts[:-1])
        return f"{surname}, {forenames}"
    else:
        # Single name or can't determine, return as is
        return author_name


def extract_publisher_from_domain(url: str) -> Optional[str]:
    """Extract publisher name from domain."""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www prefix
        if domain.startswith("www."):
            domain = domain[4:]

        # Common domain to publisher mappings
        domain_mappings = {
            "nytimes.com": "New York Times",
            "washingtonpost.com": "Washington Post",
            "cnn.com": "CNN",
            "bbc.com": "BBC",
            "reuters.com": "Reuters",
            "theguardian.com": "The Guardian",
            "wsj.com": "Wall Street Journal",
            "forbes.com": "Forbes",
            "bloomberg.com": "Bloomberg",
            "npr.org": "NPR",
            "medium.com": "Medium",
            "github.com": "GitHub",
            "stackoverflow.com": "Stack Overflow",
            "wikipedia.org": "Wikipedia",
        }

        if domain in domain_mappings:
            return domain_mappings[domain]

        # For other domains, use the domain name as publisher
        # Remove common TLDs and make it more readable
        domain_parts = domain.split(".")
        if len(domain_parts) >= 2:
            # Use the main domain part
            main_domain = domain_parts[0]
            # Capitalize first letter
            return main_domain.capitalize()

        return domain

    except Exception as e:
        logging.error(f"Error extracting publisher from domain: {e}")
        return None
