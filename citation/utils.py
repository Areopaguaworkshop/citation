import os
import subprocess
import logging
import fitz  # PyMuPDF
import requests
from urllib.parse import urlparse
from typing import Optional, Dict, Tuple
import re


import re
from pypinyin import pinyin, Style


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


def parse_page_range(page_range_str: str, total_pages: int) -> Optional[str]:
    """
    Parse a page range string (e.g., "1-5, -3") into a comma-separated list of 1-based page numbers.
    Returns None if the range is invalid or empty.
    """
    if not page_range_str:
        return None

    pages_to_process = set()
    parts = page_range_str.split(",")

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if part.startswith("-"):
            # Last N pages
            try:
                last_n = int(part)
                if last_n > 0:
                    logging.warning(f"Invalid last page range '{part}', should be negative. Skipping.")
                    continue
                start_page = max(1, total_pages + last_n + 1)
                pages_to_process.update(range(start_page, total_pages + 1))
            except ValueError:
                logging.warning(f"Invalid page range format: {part}. Skipping.")
                continue
        elif "-" in part:
            # A range of pages (e.g., "1-5")
            try:
                start, end = map(int, part.split("-"))
                if start > end:
                    logging.warning(f"Invalid page range {start}-{end}. Skipping.")
                    continue
                pages_to_process.update(range(start, min(end, total_pages) + 1))
            except ValueError:
                logging.warning(f"Invalid page range format: {part}. Skipping.")
                continue
        else:
            # A single page
            try:
                page = int(part)
                if 1 <= page <= total_pages:
                    pages_to_process.add(page)
            except ValueError:
                logging.warning(f"Invalid page number: {part}. Skipping.")

    if not pages_to_process:
        return None

    # Sort and convert to comma-separated string for ocrmypdf
    return ",".join(map(str, sorted(list(pages_to_process))))


def detect_page_numbers(pdf_path: str) -> Tuple[Optional[int], Optional[int]]:
    """Detect first and last page numbers from PDF footer, with improved robustness."""
    try:
        doc = fitz.open(pdf_path)
        if doc.page_count == 0:
            return None, None

        first_page_num = None
        last_page_num = None

        # Check first few pages for the first page number
        for page_idx in range(min(3, doc.page_count)):
            page = doc[page_idx]
            footer_text = page.get_text("text", clip=fitz.Rect(page.rect.x0, page.rect.y1 - 80, page.rect.x1, page.rect.y1))
            numbers = re.findall(r"\b(\d+)\b", footer_text)
            if numbers:
                for num_str in numbers:
                    num = int(num_str)
                    if 1 <= num <= 9999:
                        first_page_num = num - page_idx
                        break
                if first_page_num is not None:
                    break
        
        # Check last few pages for the last page number
        for i in range(doc.page_count):
            page_idx = doc.page_count - 1 - i
            if page_idx < 0 or i >= 3: # Check last 3 pages at most
                break
            
            page = doc[page_idx]
            footer_text = page.get_text("text", clip=fitz.Rect(page.rect.x0, page.rect.y1 - 80, page.rect.x1, page.rect.y1))
            numbers = re.findall(r"\b(\d+)\b", footer_text)
            
            if numbers:
                # Find the most likely candidate (often the largest number in the footer)
                candidate_nums = [int(n) for n in numbers if 1 <= int(n) <= 9999]
                if candidate_nums:
                    last_page_num = max(candidate_nums)
                    break

        doc.close()
        return first_page_num, last_page_num

    except Exception as e:
        logging.error(f"Error detecting page numbers: {e}")
        return None, None


def ensure_searchable_pdf(
    pdf_path: str, num_pages: int, lang: str = "eng+chi_sim", page_range: str = "1-5, -3"
) -> str:
    """Ensure PDF is searchable using OCR if needed, processing only the specified page range."""
    try:
        # Check if PDF is already searchable by checking the first page in the range
        doc = fitz.open(pdf_path)
        
        # Determine pages to check for text
        check_pages_str = parse_page_range(page_range, num_pages)
        if not check_pages_str:
            logging.warning("Page range resulted in no pages to process. Using original PDF.")
            return pdf_path
            
        first_page_to_check = int(check_pages_str.split(',')[0]) - 1 # 0-indexed
        
        first_page = doc[first_page_to_check]
        text = first_page.get_text()
        doc.close()

        if text.strip():
            logging.info("PDF appears to be searchable.")
            return pdf_path

        # OCR the PDF
        logging.info(f"PDF is not searchable, running OCR with lang='{lang}' on page range='{page_range}'...")

        output_dir = os.path.dirname(pdf_path) or "."
        ocr_output = os.path.join(output_dir, f"ocr_{os.path.basename(pdf_path)}")

        # Use the parsed page range for OCR
        ocr_pages = parse_page_range(page_range, num_pages)
        
        if not ocr_pages:
            logging.error("Cannot perform OCR: The specified page range is empty or invalid.")
            return pdf_path

        cmd = ["ocrmypdf", "--deskew", "--force-ocr", "-l", lang, "--pages", ocr_pages, pdf_path, ocr_output]

        logging.info(f"Running command: {' '.join(cmd)}")
        process = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

        if process.returncode == 0:
            logging.info(f"OCR completed successfully: {ocr_output}")
            print(process.stdout)
            return ocr_output
        else:
            logging.error(f"OCR failed with return code {process.returncode}.")
            logging.error(f"Stderr: {process.stderr}")
            print(process.stderr)
            return pdf_path

    except Exception as e:
        logging.error(f"Error ensuring searchable PDF: {e}")
        return pdf_path


def extract_pdf_text(pdf_path: str, doc_type: str, page_range: str = "1-5, -3") -> str:
    """Extract text from specified page range in a PDF."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        total_pages = doc.page_count
        pages_str = parse_page_range(page_range, total_pages)
        
        if not pages_str:
            logging.warning("Could not parse page range, extracting no text.")
            return ""
            
        pages_to_extract = [int(p) - 1 for p in pages_str.split(',')]

        for i in pages_to_extract:
            if 0 <= i < total_pages:
                page = doc[i]
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


def save_citation(csl_data: Dict, output_dir: str):
    """Save citation information as a CSL JSON file."""
    import json

    try:
        os.makedirs(output_dir, exist_ok=True)

        # Generate base filename from the CSL ID
        base_name = csl_data.get("id", "citation")

        # Save as JSON
        json_path = os.path.join(output_dir, f"{base_name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(csl_data, f, indent=2, ensure_ascii=False)

        logging.info(f"CSL JSON citation saved to: {json_path}")

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


def format_author_csl(author_name: str) -> list:
    """Formats an author string into a CSL-JSON compliant list of objects."""
    from pypinyin import pinyin, Style

    if not author_name or not author_name.strip():
        return []

    authors = []
    # Regex to check for Chinese characters
    is_chinese = lambda s: re.search(r'[\u4e00-\u9fff]', s)

    for name_part in author_name.split(','):
        name = name_part.strip()
        if not name:
            continue

        if is_chinese(name):
            literal_name = name
            # Chinese name parsing logic
            if len(name) in [2, 3]:
                family = name[0]
                given = name[1:]
            elif len(name) == 4:
                family = name[:2]
                given = name[2:]
            else: # Fallback for other lengths
                family = name[0]
                given = name[1:]
            
            # Convert to Pinyin
            family_pinyin = "".join(item[0] for item in pinyin(family, style=Style.NORMAL)).title()
            given_pinyin = "".join(item[0] for item in pinyin(given, style=Style.NORMAL)).title()
            
            authors.append({"family": family_pinyin, "given": given_pinyin, "literal": literal_name})
        else:
            # Western name parsing logic
            parts = name.split()
            if len(parts) >= 2:
                family = parts[-1]
                given = " ".join(parts[:-1])
                authors.append({"family": family, "given": given})
            else:
                authors.append({"literal": name}) # Treat as a single literal name if structure is unclear
    
    return authors


def to_csl_json(data: Dict, doc_type: str) -> Dict:
    """Converts the internal dictionary to a CSL-JSON compliant dictionary."""
    csl = {}

    # 1. Map Type
    type_mapping = {
        "book": "book",
        "thesis": "thesis",
        "journal": "article-journal",
        "bookchapter": "chapter",
        "url": "webpage",
        "media": "motion_picture", # Default for media, can be refined
        "video": "motion_picture",
        "audio": "song",
    }
    csl["type"] = type_mapping.get(doc_type, "document") # Fallback to 'document'

    # 2. Format Authors and Editors
    if "author" in data:
        csl["author"] = format_author_csl(data["author"])
    if "editor" in data:
        csl["editor"] = format_author_csl(data["editor"])

    # 3. Format Dates
    if "year" in data:
        try:
            # Attempt to parse a full date if available, otherwise just use year
            date_parts = [int(p) for p in str(data.get("date", data["year"])).split('-')]
            csl["issued"] = {"date-parts": [date_parts]}
        except:
            csl["issued"] = {"date-parts": [[int(data["year"])]]}
            
    if "date_accessed" in data:
        try:
            date_parts = [int(p) for p in data["date_accessed"].split('-')]
            csl["accessed"] = {"date-parts": [date_parts]}
        except:
            pass # Don't add if format is wrong

    # 4. Map Fields
    field_mapping = {
        "title": "title",
        "publisher": "publisher",
        "city": "publisher-place",
        "journal": "container-title",
        "volume": "volume",
        "issue": "issue",
        "pages": "page",
        "url": "URL",
        "doi": "DOI",
        "isbn": "ISBN",
    }
    for old_key, new_key in field_mapping.items():
        if old_key in data:
            csl[new_key] = data[old_key]

    # 5. Generate ID
    id_parts = []
    if csl.get("author"):
        id_parts.append(csl["author"][0].get("family", "").lower())
    if csl.get("issued"):
        id_parts.append(str(csl["issued"]["date-parts"][0][0]))
    if csl.get("title"):
        id_parts.append(csl["title"].split()[0].lower())
    
    csl["id"] = "-".join(p for p in id_parts if p)
    if not csl["id"]:
        csl["id"] = "citation-" + os.urandom(4).hex() # Fallback ID

    return csl


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
