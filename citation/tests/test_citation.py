import os
import pytest
from citation import CitationExtractor

TEST_PDF_DIR = "examples"
TEST_URL = "http://example.com/sample-article"

@pytest.mark.parametrize("pdf_file", [
    "sample-english.pdf",
    "sample-chinese.pdf",
])
def test_pdf_extraction(pdf_file):
    extractor = CitationExtractor()
    pdf_path = os.path.join(TEST_PDF_DIR, pdf_file)
    
    citation_info = extractor.extract_from_pdf(pdf_path)
    assert citation_info is not None, f"Failed to extract citation for {pdf_file}"
    
    # Verify expected keys
    expected_keys = {'title', 'author'}
    if pdf_file == "sample-chinese.pdf":
        expected_keys.add('year')
    
    for key in expected_keys:
        assert key in citation_info, f"Missing key {key} for {pdf_file}"
    
    # Check output files exist
    base_name = os.path.splitext(pdf_file)[0]
    yaml_path = os.path.join(TEST_PDF_DIR, f"{base_name}.yaml")
    json_path = os.path.join(TEST_PDF_DIR, f"{base_name}.json")
    assert os.path.exists(yaml_path), "Output YAML missing"
    assert os.path.exists(json_path), "Output JSON missing"


def test_url_extraction():
    extractor = CitationExtractor()
    citation_info = extractor.extract_from_url(TEST_URL)
    assert citation_info is not None, "Failed to extract citation from URL"
    assert 'title' in citation_info, "Missing title in URL citation"
    assert 'author' in citation_info, "Missing author in URL citation"
