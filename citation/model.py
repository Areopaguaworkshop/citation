import dspy
import logging
from typing import Dict, Optional
from .llm import get_llm_model


class CitationLLM:
    """LLM handler for citation extraction using DSPy."""

    def __init__(self, llm_model="ollama/qwen3"):
        """Initialize the LLM."""
        self.llm = get_llm_model(llm_model)
        dspy.settings.configure(lm=self.llm)

    def _truncate_text(self, text: str, max_tokens: int = 2048) -> str:
        """Truncate text to a maximum number of tokens."""
        tokens = text.split()
        if len(tokens) > max_tokens:
            return " ".join(tokens[:max_tokens])
        return text

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
                "pdf_text -> title, author, container_title, year, volume, issue, page_numbers, isbn, doi",
                "Extract citation information from journal PDF text. Focus on first page header and footer. "
                "Look for title in first line with biggest font size, author usually right under the title. "
                "Find journal name (as container_title), year, volume, and issue number in header or footer of first page. "
                "Page numbers format should be 'start-end' (e.g., '20-41'). "
                "For Chinese text, extract information similarly. Return 'Unknown' for missing fields.",
            )

            predictor = dspy.Predict(signature)
            result = predictor(pdf_text=pdf_text)

            # Convert result to dictionary
            citation_info = {}
            for key, value in result.items():
                if value and value.strip() and value.strip().lower() != "unknown":
                    # Convert container_title back to container-title for compatibility
                    if key == "container_title":
                        citation_info["container-title"] = value.strip()
                    else:
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
                "pdf_text -> title, author, container_title, editor, publisher, year, location, page_numbers, isbn, doi",
                "Analyze the text from a book chapter and extract its citation metadata. "
                "Identify the following fields: "
                "- title: The title of the chapter itself. "
                "- author: The author(s) of the chapter. "
                "- container-title: The title of the book that contains the chapter. "
                "- editor: The editor(s) of the book, often found near 'edited by'. "
                "- publisher: The publisher of the book. "
                "- year: The publication year of the book. "
                "- page_numbers: The page range of the chapter (e.g., '20-41'). "
                "- location, isbn, doi: If available. "
                "For Chinese text, extract the information similarly. If a field is not found, return 'Unknown'.",
            )

            predictor = dspy.Predict(signature)
            result = predictor(pdf_text=pdf_text)

            # Convert result to dictionary
            citation_info = {}
            for key, value in result.items():
                if value and value.strip() and value.strip().lower() != "unknown":
                    # Convert container_title back to container-title for compatibility
                    if key == "container_title":
                        citation_info["container-title"] = value.strip()
                    else:
                        citation_info[key] = value.strip()

            logging.info(f"Book chapter LLM extraction result: {citation_info}")
            return citation_info

        except Exception as e:
            logging.error(f"Error with book chapter LLM extraction: {e}")
            return {}

    def extract_citation_from_text(self, text: str, doc_type: str) -> Dict:
        """Extract citation based on document type after truncating long text."""
        truncated_text = self._truncate_text(text)

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

