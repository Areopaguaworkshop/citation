import os
import pytest
from citation import CitationExtractor
from citation.utils import guess_title_from_filename, detect_page_numbers

TEST_PDF_DIR = "examples"
TEST_URL = "https://www.example.com"

def test_url_extraction():
    """Test URL citation extraction."""
    extractor = CitationExtractor()
    citation_info = extractor.extract_citation(TEST_URL)
    assert citation_info is not None, "Failed to extract citation from URL"
    assert 'URL' in citation_info, "Missing URL in citation"
    assert 'accessed' in citation_info, "Missing date_accessed in citation"

def test_auto_detection_url():
    """Test auto-detection of URL input."""
    extractor = CitationExtractor()
    citation_info = extractor.extract_citation(TEST_URL)
    assert citation_info is not None, "Failed to extract citation from URL"
    assert citation_info['URL'] == TEST_URL, "URL not correctly saved"

def test_auto_detection_nonexistent_file():
    """Test auto-detection with nonexistent file."""
    extractor = CitationExtractor()
    citation_info = extractor.extract_citation("nonexistent.pdf")
    assert citation_info is None, "Should return None for nonexistent file"

def test_invalid_input():
    """Test invalid input handling."""
    extractor = CitationExtractor()
    citation_info = extractor.extract_citation("invalid input")
    assert citation_info is None, "Should return None for invalid input"

def test_filename_guessing():
    """Test filename title guessing functionality."""
    # Test good filenames
    assert guess_title_from_filename("paper_machine_learning_final.pdf") == "machine learning"
    assert guess_title_from_filename("draft_neural_networks_v2.pdf") == "neural networks"
    assert guess_title_from_filename("2024_deep_learning_submitted.pdf") == "deep learning"
    assert guess_title_from_filename("article_natural_language_processing.pdf") == "natural language processing"
    
    # Test bad filenames
    assert guess_title_from_filename("abc.pdf") is None
    assert guess_title_from_filename("test.pdf") == "test"
    assert guess_title_from_filename("document.pdf") is None

def test_document_type_override():
    """Test document type override functionality."""
    extractor = CitationExtractor()
    
    # Test with non-existent file to check type handling
    # This should fail gracefully but we can check the parameter passing
    citation_info = extractor.extract_citation("nonexistent.pdf", doc_type_override="thesis")
    assert citation_info is None, "Should return None for nonexistent file"

# TODO: Add PDF tests when example PDFs are available
# def test_pdf_extraction_with_type():
#     """Test PDF extraction with specific document type."""
#     extractor = CitationExtractor()
#     pdf_path = os.path.join(TEST_PDF_DIR, "sample.pdf")
#     
#     # Test with different document types
#     for doc_type in ["book", "thesis", "journal", "bookchapter"]:
#         citation_info = extractor.extract_citation(pdf_path, doc_type_override=doc_type)
#         if citation_info:
#             assert 'title' in citation_info or 'author' in citation_info, f"No useful info for {doc_type}"
