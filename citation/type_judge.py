import logging
import re
from typing import Tuple

import fitz  # PyMuPDF


def is_thesis(pdf_path: str) -> bool:
    """
    Check if the document is a thesis by searching for keywords in the text
    of the pages specified by the page range.
    """
    # Keywords to identify a thesis, including common English and Chinese terms
    thesis_keywords = [
        'thesis', 'dissertation', 'phd', 'master',
        '论文', '博士', '硕士'
    ]
    # Compile a single regex for case-insensitive matching
    # \b ensures we match whole words
    keyword_regex = re.compile(r'\b(' + '|'.join(thesis_keywords) + r')\b', re.IGNORECASE)

    try:
        doc = fitz.open(pdf_path)
        # Iterate through all pages of the (subset) PDF
        for page in doc:
            text = page.get_text("text")
            if keyword_regex.search(text):
                logging.info(f"Thesis keyword found on page {page.number + 1}.")
                doc.close()
                return True
        doc.close()
    except Exception as e:
        logging.error(f"Error checking for thesis keywords in {pdf_path}: {e}")
    
    return False


def differentiate_article_or_chapter(pdf_path: str) -> str:
    """
    Differentiates between a journal article and a book chapter using a clear, rule-based hierarchy.
    Defaults to 'journal' if no definitive indicators are found.
    """
    try:
        doc = fitz.open(pdf_path)
        if doc.page_count == 0:
            return "journal"  # Default

        # Analyze text from header, footer, and full first page for efficiency
        text_to_analyze = ""
        for i in range(min(doc.page_count, 5)): # Check first 5 pages
            page = doc[i]
            if i == 0: # Get full text of first page
                text_to_analyze += page.get_text().lower() + "\n"
            else: # Get only header/footer for other pages
                rect = page.rect
                header_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + rect.height * 0.15)
                footer_rect = fitz.Rect(rect.x0, rect.y1 - rect.height * 0.15, rect.x1, rect.y1)
                text_to_analyze += page.get_text(clip=header_rect).lower() + "\n"
                text_to_analyze += page.get_text(clip=footer_rect).lower() + "\n"

        # --- Rule-Based Judging ---

        # Rule 1: High-confidence chapter keywords (immediate decision)
        chapter_knockout_keywords = [
            'edited by', 'editor', 'isbn', 'press', 'herausgeber', 'éditeur', '主编', '出版社'
        ]
        for keyword in chapter_knockout_keywords:
            if keyword in text_to_analyze:
                logging.info(f"Classified as BOOKCHAPTER based on knockout keyword: '{keyword}'")
                doc.close()
                return "bookchapter"

        # Rule 2: High-confidence journal keywords
        journal_knockout_keywords = [
            'issn', 'journal', 'proceedings', 'zeitschrift', 'revue', '学报', '期刊'
        ]
        for keyword in journal_knockout_keywords:
            if keyword in text_to_analyze:
                logging.info(f"Classified as JOURNAL based on knockout keyword: '{keyword}'")
                doc.close()
                return "journal"

        # Rule 3: Journal-specific patterns
        has_volume = re.search(r'\b(volume|vol\.)\b', text_to_analyze)
        has_issue = re.search(r'\b(issue|no\.)\b', text_to_analyze)
        if has_volume and has_issue:
            logging.info("Classified as JOURNAL based on presence of 'volume' and 'issue'")
            doc.close()
            return "journal"

        first_page_num, _ = detect_page_numbers(pdf_path)
        if first_page_num and first_page_num > 100:
            logging.info(f"Classified as JOURNAL based on high starting page number: {first_page_num}")
            doc.close()
            return "journal"

        doc.close()

    except Exception as e:
        logging.error(f"Error during article/chapter differentiation: {e}")
        return "journal" # Default on error

    # Rule 4: Default
    logging.info("No definitive indicators found. Defaulting to JOURNAL.")
    return "journal"


def determine_document_type(pdf_path: str, num_pages: int) -> str:
    """
    Determines the document type by orchestrating checks for thesis, book,
    journal, or book chapter.
    """
    if num_pages >= 70:
        if is_thesis(pdf_path):
            return "thesis"
        else:
            return "book"
    else:
        # For shorter documents, differentiate between journal and chapter
        return differentiate_article_or_chapter(pdf_path)


def detect_page_numbers(pdf_path: str) -> Tuple[int, int]:
    """
    Detects the first and last page numbers from the text, typically in the footer.
    This is a helper for the differentiation logic.
    """
    first_page_num, last_page_num = None, None
    try:
        doc = fitz.open(pdf_path)
        if doc.page_count == 0:
            return None, None

        # Check first few pages for the first page number
        for page_idx in range(min(3, doc.page_count)):
            page = doc[page_idx]
            footer_text = page.get_text("text", clip=fitz.Rect(page.rect.x0, page.rect.y1 - 80, page.rect.x1, page.rect.y1))
            numbers = re.findall(r'\b(\d+)\b', footer_text)
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
            numbers = re.findall(r'\b(\d+)\b', footer_text)
            
            if numbers:
                candidate_nums = [int(n) for n in numbers if 1 <= int(n) <= 9999]
                if candidate_nums:
                    last_page_num = max(candidate_nums)
                    break

        doc.close()
        return first_page_num, last_page_num
    except Exception as e:
        logging.error(f"Error detecting page numbers: {e}")
        return None, None
