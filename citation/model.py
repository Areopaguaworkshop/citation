import dspy
import logging
from typing import Dict, Optional
from .llm import get_llm_model


def _truncate_text(text: str, max_length: int = 8192) -> str:
    """Truncates text to a max length, keeping start and end."""
    if len(text) <= max_length:
        return text
    
    half_length = max_length // 2
    return (
        text[:half_length]
        + "\n\n... (text truncated for brevity) ...\n\n"
        + text[-half_length:]
    )


class CitationLLM:
    """LLM handler for citation extraction using DSPy."""

    def __init__(self, llm_model="ollama/qwen3"):
        """Initialize the LLM."""
        self.llm = get_llm_model(llm_model)
        dspy.settings.configure(lm=self.llm)

    def extract_book_citation(self, pdf_text: str) -> Dict:
        """Extract citation from book PDF text."""
        try:
            signature = dspy.Signature(
                "pdf_text -> title, author, publisher, year, location, editor, translator, volume, series, isbn, doi",
                "Extract citation information from book PDF text. Focus on cover and copyright pages (usually in first 5 pages). "
                "Look for title in the middle and upper part with biggest font size, author usually right under the title. "
                "In copyright page, find publish year and publisher. For Chinese text, extract information similarly. "
                "Return 'Unknown' for missing fields.",
            )

            predictor = dspy.Predict(signature)
            result = predictor(pdf_text=pdf_text)

            # Convert result to dictionary
            citation_info = {}
            for key, value in result.items():
                if value and value.strip() and value.strip().lower() != "unknown":
                    citation_info[key] = value.strip()

            logging.info(f"Book LLM extraction result: {citation_info}")
            return citation_info

        except Exception as e:
            logging.error(f"Error with book LLM extraction: {e}")
            return {}

    def extract_thesis_citation(self, pdf_text: str) -> Dict:
        """Extract citation from thesis PDF text."""
        try:
            signature = dspy.Signature(
                "pdf_text -> title, author, thesis_type, year, publisher, location, doi",
                "Extract citation information from thesis PDF text. Focus on cover and title pages (usually in first 5 pages). "
                "Look for title in the middle and upper part with biggest font size, author usually right under the title. "
                "Identify if it's a PhD thesis or Master thesis. Publisher should be a university or college. "
                "For Chinese text, extract information similarly. Return 'Unknown' for missing fields.",
            )

            predictor = dspy.Predict(signature)
            result = predictor(pdf_text=pdf_text)

            # Convert result to dictionary
            citation_info = {}
            for key, value in result.items():
                if value and value.strip() and value.strip().lower() != "unknown":
                    citation_info[key] = value.strip()

            logging.info(f"Thesis LLM extraction result: {citation_info}")
            return citation_info

        except Exception as e:
            logging.error(f"Error with thesis LLM extraction: {e}")
            return {}

    def extract_journal_citation(self, pdf_text: str) -> Dict:
        """Extract citation from journal PDF text."""
        try:
            signature = dspy.Signature(
                "pdf_text -> title, author, journal_name, year, volume, number, page_numbers, isbn, doi",
                "Extract citation information from journal PDF text. Focus on first page header and footer. "
                "Look for title in first line with biggest font size, author usually right under the title. "
                "Find journal name, year, volume, and issue number in header or footer of first page. "
                "Page numbers format should be 'start-end' (e.g., '20-41'). "
                "For Chinese text, extract information similarly. Return 'Unknown' for missing fields.",
            )

            predictor = dspy.Predict(signature)
            result = predictor(pdf_text=pdf_text)

            # Convert result to dictionary
            citation_info = {}
            for key, value in result.items():
                if value and value.strip() and value.strip().lower() != "unknown":
                    citation_info[key] = value.strip()

            logging.info(f"Journal LLM extraction result: {citation_info}")
            return citation_info

        except Exception as e:
            logging.error(f"Error with journal LLM extraction: {e}")
            return {}

    def extract_bookchapter_citation(self, pdf_text: str) -> Dict:
        """Extract citation from book chapter PDF text."""
        try:
            signature = dspy.Signature(
                "pdf_text -> title, author, book_name, editor, publisher, year, location, page_numbers, isbn, doi",
                "Extract citation information from book chapter PDF text. The first three pages may contain book name and editor. "
                "First, find parent book title (book_name), book editor, publisher, and year in the first 1-4 pages, look the 'edited by' should follows editors . "
                "Second, Look for chapter title and chapter author within first 10 pages, The title will be big font-size in the first 1-2 lines, the author will right below it. "
                "Thrid, find page numbers format should be 'start-end' (e.g., '20-41') on the footer or header with continue int.. "
                "For Chinese text, extract information similarly. Return 'Unknown' for missing fields.",
            )

            predictor = dspy.Predict(signature)
            result = predictor(pdf_text=pdf_text)

            # Convert result to dictionary
            citation_info = {}
            for key, value in result.items():
                if value and value.strip() and value.strip().lower() != "unknown":
                    citation_info[key] = value.strip()

            logging.info(f"Book chapter LLM extraction result: {citation_info}")
            return citation_info

        except Exception as e:
            logging.error(f"Error with book chapter LLM extraction: {e}")
            return {}

    def extract_citation_from_text(self, text: str, doc_type: str) -> Dict:
        """Extract citation based on document type after truncating long text."""
        
        # Truncate the text to a reasonable length before sending to LLM
        truncated_text = _truncate_text(text)
        if len(text) != len(truncated_text):
            logging.info(f"Text truncated: original {len(text)} chars, now {len(truncated_text)} chars.")

        if doc_type == "book":
            return self.extract_book_citation(truncated_text)
        elif doc_type == "thesis":
            return self.extract_thesis_citation(truncated_text)
        elif doc_type == "journal":
            return self.extract_journal_citation(truncated_text)
        elif doc_type == "bookchapter":
            return self.extract_bookchapter_citation(truncated_text)
        else:
            # Default fallback
            logging.warning(f"Unknown document type: {doc_type}, using book extraction")
            return self.extract_book_citation(truncated_text)