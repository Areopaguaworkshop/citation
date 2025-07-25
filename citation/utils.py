import os
import subprocess
import logging
import fitz  # PyMuPDF
import requests
from urllib.parse import urlparse
from typing import Optional, Dict, Tuple, List
import re
import tempfile


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


def parse_page_range(page_range_str: str, total_pages: int) -> List[int]:
    """
    Parse a page range string (e.g., "1-5, -3") into a sorted list of 1-based page numbers.
    Returns an empty list if the range is invalid or empty.
    """
    if not page_range_str:
        return []

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
                    logging.warning(
                        f"Invalid last page range '{
                            part}', should be negative. Skipping."
                    )
                    continue
                start_page = max(1, total_pages + last_n + 1)
                pages_to_process.update(range(start_page, total_pages + 1))
            except ValueError:
                logging.warning(f"Invalid page range format: {
                                part}. Skipping.")
                continue
        elif "-" in part:
            # A range of pages (e.g., "1-5")
            try:
                start, end = map(int, part.split("-"))
                if start > end:
                    logging.warning(f"Invalid page range {
                                    start}-{end}. Skipping.")
                    continue
                pages_to_process.update(
                    range(start, min(end, total_pages) + 1))
            except ValueError:
                logging.warning(f"Invalid page range format: {
                                part}. Skipping.")
                continue
        else:
            # A single page
            try:
                page = int(part)
                if 1 <= page <= total_pages:
                    pages_to_process.add(page)
            except ValueError:
                logging.warning(f"Invalid page number: {part}. Skipping.")

    return sorted(list(pages_to_process))


def ensure_searchable_pdf(pdf_path: str, lang: str = "eng+chi_sim") -> str:
    """Ensure PDF is searchable using OCR if needed."""
    try:
        doc = fitz.open(pdf_path)
        # Check if the first page has text. A more robust check might be needed
        # for PDFs with mixed image/text pages.
        if doc.page_count > 0 and doc[0].get_text().strip():
            logging.info("PDF appears to be searchable.")
            doc.close()
            return pdf_path
        doc.close()

        logging.info(
            f"PDF is not searchable or empty, running OCR with lang='{
                lang}'..."
        )

        # Create a path for the OCR'd file in the same directory
        output_dir = os.path.dirname(pdf_path) or "."
        base_name = os.path.basename(pdf_path)
        ocr_output_path = os.path.join(output_dir, f"ocr_{base_name}")

        cmd = [
            "ocrmypdf",
            "--deskew",
            "--force-ocr",
            "-l",
            lang,
            pdf_path,
            ocr_output_path,
        ]

        logging.info(f"Running command: {' '.join(cmd)}")
        process = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )

        if process.returncode == 0:
            logging.info(f"OCR completed successfully: {ocr_output_path}")
            # If the original path was a temp file, remove it as we now have the OCR'd version
            if "temp" in pdf_path.lower() and os.path.basename(pdf_path).startswith(
                "tmp"
            ):
                os.remove(pdf_path)
            return ocr_output_path
        else:
            logging.error(f"OCR failed with return code {process.returncode}.")
            logging.error(f"Stderr: {process.stderr}")
            # Return original path on failure
            return pdf_path

    except Exception as e:
        logging.error(f"Error in ensure_searchable_pdf: {e}")
        return pdf_path


def create_subset_pdf(
    pdf_path: str, page_range: str, total_pages: int
) -> Optional[str]:
    """
    Creates a temporary PDF file containing only the pages specified in the page range.
    Returns the path to the temporary file, or None if failed.
    """
    pages_to_include = parse_page_range(page_range, total_pages)
    if not pages_to_include:
        logging.error("Failed to create subset PDF: No valid pages specified.")
        return None

    try:
        source_doc = fitz.open(pdf_path)
        new_doc = fitz.open()  # Create a new, empty PDF

        # Convert 1-based page numbers to 0-based indices
        page_indices = [p - 1 for p in pages_to_include]

        # Insert each page individually to handle non-contiguous ranges
        for page_idx in page_indices:
            if 0 <= page_idx < source_doc.page_count:
                new_doc.insert_pdf(source_doc, from_page=page_idx, to_page=page_idx)

        # Create a temporary file to save the new PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_path = temp_file.name

        new_doc.save(temp_path, garbage=4, deflate=True, clean=True)

        source_doc.close()
        new_doc.close()

        logging.info(
            f"Created temporary subset PDF with {len(pages_to_include)} pages at: {temp_path}"
        )
        return temp_path

    except Exception as e:
        logging.error(f"Error creating subset PDF: {e}")
        if "temp_path" in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return None


def extract_pdf_text(pdf_path: str, page_number: int) -> str:
    """Extract text from a specific page in a PDF."""
    try:
        doc = fitz.open(pdf_path)
        if 0 <= page_number < doc.page_count:
            page = doc[page_number]
            text = page.get_text()
            doc.close()
            return text
        else:
            logging.warning(
                f"Page number {page_number} is out of range for PDF with {
                    doc.page_count} pages."
            )
            doc.close()
            return ""
    except Exception as e:
        logging.error(f"Error extracting text from page {
                      page_number} of PDF: {e}")
        return ""


def determine_url_type(url: str) -> str:
    """Determine URL type with enhanced platform detection."""
    try:
        # First, check for known video/audio platforms by domain
        from urllib.parse import urlparse
        parsed_url = urlparse(url.lower())
        domain = parsed_url.netloc.replace("www.", "")
        
        # Video platforms - these should return "media" for motion_picture CSL type
        video_platforms = {
            "youtube.com",
            "youtu.be", 
            "vimeo.com",
            "dailymotion.com", 
            "twitch.tv",
            "tiktok.com",
            "bilibili.com",
            "rumble.com",
        }
        
        # Audio platforms
        audio_platforms = {
            "soundcloud.com",
            "spotify.com", 
            "anchor.fm",
            "podcasts.google.com",
        }
        
        # Check video platforms first
        if domain in video_platforms:
            return "media"  # This will trigger motion_picture CSL type
        
        # Check audio platforms  
        if domain in audio_platforms:
            return "media"  # This will trigger motion_picture CSL type
        
        # For social media platforms, check URL patterns for video content
        if domain in ["facebook.com", "instagram.com", "twitter.com", "x.com"]:
            if any(pattern in url.lower() for pattern in ["/video/", "/watch/", "/reel/", "/status/"]):
                return "media"
        
        # Fallback to header-based detection for other URLs
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


# Patterns for author titles/honorifics in English and Chinese
AUTHOR_TITLES = [
    "Dr.", "Fr.", "Professor", "Prof.",
    "博士", "神父", "教授", "老师", "先生"
]

def format_author_csl(author_name: str) -> list:
    """Formats an author string into a CSL-JSON compliant list of objects."""
    from pypinyin import pinyin, Style

    if not author_name or not author_name.strip():
        return []

    authors = []
    # Regex to check for CJK and Latin characters
    def is_cjk(s): return re.search(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", s)
    def is_latin(s): return re.search(r"[a-zA-Z]", s)

    # Step 1: Smart Separation for multiple authors
    processed_author_name = re.sub(r"[\n;,、]", ",", author_name)
    # Add a comma between CJK characters and Latin characters to help splitting
    processed_author_name = re.sub(r'([\u4e00-\u9fff])\s+([a-zA-Z])', r'\1,\2', processed_author_name)
    processed_author_name = re.sub(r'([a-zA-Z])\s+([\u4e00-\u9fff])', r'\1,\2', processed_author_name)
    # Add a comma between CJK names separated by space
    processed_author_name = re.sub(r'([\u4e00-\u9fff]{2,})\s+([\u4e00-\u9fff]{2,})', r'\1,\2', processed_author_name)


    name_parts = re.split(r'\s+and\s+|,', processed_author_name, flags=re.IGNORECASE)

    # Step 2: Formatting Individual Names
    for name in name_parts:
        name = name.strip()
        if not name:
            continue

        # Step 2a: Extract Suffix/Title
        suffix = None
        for title in AUTHOR_TITLES:
            if name.endswith(f" {title}") or name.endswith(title):
                suffix = title
                name = name[:-len(title)].strip()
                break
        
        author_obj = {}

        # Step 2b: Parse the name
        if is_cjk(name) and not is_latin(name): # Pure CJK name
            literal_name = name
            if len(name) in [2, 3, 4]:
                family = name[0]
                given = name[1:]
                if len(name) == 4:
                    family = name[:2]
                    given = name[2:]
            else:
                family = name[0]
                given = name[1:]
            
            try:
                family_pinyin = "".join(item[0] for item in pinyin(family, style=Style.NORMAL)).title()
                given_pinyin = "".join(item[0] for item in pinyin(given, style=Style.NORMAL)).title()
                author_obj = {"family": family_pinyin, "given": given_pinyin, "literal": literal_name}
            except:
                author_obj = {"literal": literal_name}
        else: # Western or mixed-language name
            parts = name.split()
            if len(parts) >= 2:
                family = parts[-1]
                given = " ".join(parts[:-1])
                author_obj = {"family": family, "given": given}
            else:
                author_obj = {"literal": name}

        if suffix:
            author_obj["suffix"] = suffix
        
        authors.append(author_obj)

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
        "media": "motion_picture",  # Default for media, can be refined
        "video": "motion_picture",
        "motion_picture": "motion_picture",
        "audio": "song",
    }
    csl["type"] = type_mapping.get(
        doc_type, "document")  # Fallback to 'document'

    # 2. Format Authors and Editors
    if "author" in data:
        csl["author"] = format_author_csl(data["author"])
    if "editor" in data:
        csl["editor"] = format_author_csl(data["editor"])

    # 3. Format Dates
    if "date" in data or "year" in data:
        try:
            # Attempt to parse a full date if available, otherwise just use year
            date_str = str(data.get("date", data.get("year")))
            date_parts = [int(p) for p in date_str.split("-")]
            csl["issued"] = {"date-parts": [date_parts]}
        except (ValueError, TypeError):
            if "year" in data:
                try:
                    csl["issued"] = {"date-parts": [[int(data["year"])]]}
                except (ValueError, TypeError):
                    pass # Ignore if year is not a valid integer
    
    if "date_accessed" in data:
        try:
            date_parts = [int(p) for p in data["date_accessed"].split("-")]
            csl["accessed"] = {"date-parts": [date_parts]}
        except:
            pass  # Don't add if format is wrong

    # 4. Map Fields
    field_mapping = {
        "title": "title",
        "publisher": "publisher",
        "city": "publisher-place",
        "container-title": "container-title",
        "volume": "volume",
        "issue": "issue",
        "page_numbers": "page",
        "url": "URL",
        "doi": "DOI",
        "isbn": "ISBN",
        "genre": "genre",
        "abstract": "abstract",
        "keyword": "keyword",
    }
    for old_key, new_key in field_mapping.items():
        if old_key in data:
            csl[new_key] = data[old_key]

    # 5. Generate ID
    id_parts = []
    if csl.get("author"):
        author = csl["author"][0]
        # Use pinyin version if available
        family_name = author.get("family", "")
        given_name = author.get("given", "")
        if family_name:
            id_parts.append(family_name)
        if given_name:
            id_parts.append(given_name)

    if csl.get("issued"):
        id_parts.append(str(csl["issued"]["date-parts"][0][0]))

    if csl.get("title"):
        title = csl["title"]
        # Shorten title if it's too long
        if len(title) > 100:
            title = " ".join(title.split()[:20])  # take first 5 words
        id_parts.append(title)

    if csl.get("publisher"):
        id_parts.append(csl.get("publisher"))

    # Function to clean each part for the ID
    def clean_for_id(part):
        # Remove non-alphanumeric characters except for spaces and hyphens
        part = str(part)  # Ensure part is a string
        part = re.sub(r"[^\w\s-]", "", part).strip()
        # Replace spaces and hyphens with a single underscore
        part = re.sub(r"[\s-]+", "_", part)
        return part

    # Clean and join the parts
    cleaned_parts = [clean_for_id(p) for p in id_parts if p]
    base_id = "_".join(cleaned_parts)

    if not base_id:
        csl["id"] = "citation-" + os.urandom(4).hex() + ".md"  # Fallback ID
    else:
        csl["id"] = base_id + ".md"

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

