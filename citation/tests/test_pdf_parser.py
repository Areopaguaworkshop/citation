import unittest
from unittest.mock import patch, MagicMock
from ..parsers.pdf_parser import parse_pdf, extract_metadata

class TestPDFParser(unittest.TestCase):
    def setUp(self):
        self.test_file_path = "example/RenGuan-2020-唐朝墩古浴场.pdf"
    
    @patch('pypdf.PdfReader')
    def test_page_threshold_book(self, mock_pdf_reader):
        # Mock a PDF with 100 pages (above threshold)
        mock_instance = MagicMock()
        mock_instance.metadata = {'/Title': 'Test Book', '/Author': 'Test Author'}
        mock_pdf_reader.return_value = mock_instance
        mock_instance.pages = [MagicMock()] * 100  # Mock 100 pages

        result = parse_pdf(self.test_file_path, page_threshold=50)
        self.assertEqual(result['citation_type'], 'book')
        self.assertEqual(result['pages'], 'pp. 1-100')

    @patch('pypdf.PdfReader')
    def test_page_threshold_article(self, mock_pdf_reader):
        # Mock a PDF with 10 pages (below threshold)
        mock_instance = MagicMock()
        mock_instance.metadata = {'/Title': 'Test Article', '/Author': 'Test Author'}
        mock_pdf_reader.return_value = mock_instance
        mock_instance.pages = [MagicMock()] * 10  # Mock 10 pages

        result = parse_pdf(self.test_file_path, page_threshold=50)
        self.assertEqual(result['citation_type'], 'article')
        self.assertEqual(result['pages'], 'pp. 1-10')

    @patch('pypdf.PdfReader')
    def test_thesis_detection(self, mock_pdf_reader):
        # Mock a PDF with "thesis" in filename
        mock_instance = MagicMock()
        mock_instance.metadata = {'/Title': 'Test Thesis', '/Author': 'Test Author'}
        mock_pdf_reader.return_value = mock_instance
        mock_instance.pages = [MagicMock()] * 100  # Mock 100 pages

        result = parse_pdf("path/to/my_thesis.pdf", page_threshold=50)
        self.assertEqual(result['citation_type'], 'thesis')

    def test_error_handling(self):
        # Test with non-existent file
        result = parse_pdf("non_existent.pdf")
        self.assertIn('error', result)
        self.assertEqual(result['type'], 'pdf')