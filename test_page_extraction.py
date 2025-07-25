#!/usr/bin/env python3
"""
Test script for enhanced page number extraction with alternating position support
"""

import logging
import sys
import os
from pathlib import Path
import pytest

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from citation.model import ImprovedPageNumberExtractor, CitationLLM

# Configure logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# This test requires a specific PDF file and is intended for manual runs.
# It is skipped by default in the automated test suite.
# To run this test:
# 1. Make sure you have a PDF file for testing.
# 2. Run from the command line:
#    python test_page_extraction.py /path/to/your/pdf_file.pdf
@pytest.mark.skip(reason="Manual test that requires a specific PDF file path.")
def test_page_extraction_manual(pdf_path: str):
    """Test the enhanced page number extraction"""
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return
    
    print(f"\n=== Testing Enhanced Page Number Extraction ===")
    print(f"PDF: {pdf_path}")
    
    # Test the enhanced pattern-based extractor directly
    extractor = ImprovedPageNumberExtractor()
    
    try:
        import fitz
        doc = fitz.open(pdf_path)
        total_pages = doc.page_count
        doc.close()
        
        print(f"Total PDF pages: {total_pages}")
        
        # Test with different page ranges
        page_ranges = [
            "1-5, -3",  # First 5 and last 3
            "1-3, -2",  # First 3 and last 2
            "1-2",      # Just first 2
            "-2"        # Just last 2
        ]
        
        for page_range in page_ranges:
            print(f"\n--- Testing page range: '{page_range}' ---")
            
            sequence = extractor.find_continuous_page_sequence_with_range(
                pdf_path, page_range, total_pages
            )
            
            if sequence:
                page_numbers = list(sequence.values())
                start_page = min(page_numbers)
                end_page = max(page_numbers)
                print(f"✓ Pattern extraction found: {start_page}-{end_page}")
                print(f"  Sequence mapping: {sequence}")
            else:
                print("✗ No pattern found")
    
    except Exception as e:
        print(f"Error in pattern extraction: {e}")
    
    # Test the complete LLM extraction method
    print(f"\n--- Testing Complete LLM Method ---")
    try:
        llm = CitationLLM()
        result = llm.extract_page_numbers_for_journal_chapter(pdf_path, "1-5, -3")
        
        if result and 'page_numbers' in result:
            print(f"✓ LLM extraction found: {result['page_numbers']}")
        else:
            print("✗ LLM extraction failed")
    
    except Exception as e:
        print(f"Error in LLM extraction: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_page_extraction.py <pdf_path>")
        print("Example: python test_page_extraction.py /path/to/Bai-Yudong-白玉冬-2018-丝路景教与汪古渊流.pdf")
        sys.exit(1)
    
    pdf_path_arg = sys.argv[1]
    
    # We define a simple function to call the test function
    # so that pytest does not try to run it directly.
    def run_manual_test():
        # Since the test function is marked as skipped, we call it directly here
        # for the manual run. We need to unwrap it from the pytest marker.
        test_page_extraction_manual.__wrapped__(pdf_path_arg)

    run_manual_test()