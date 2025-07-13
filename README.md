# Citation Extractor

A tool to extract citations from PDF files and URLs in Chicago Author-Date style.

## Features

- **Auto-detection**: Automatically detects whether input is a PDF file or URL
- Extract citations from PDF files (books, theses, journals, book chapters)
- Extract citations from URLs (web articles, videos, etc.)
- Support for English and Chinese content
- Output in both YAML and JSON formats
- Multi-step extraction workflow with fallbacks

## Installation

Install dependencies using Rye:

```bash
rye sync
```

## Usage

### Command Line Interface

The CLI automatically detects input type:

```bash
# Extract citation from a PDF file
citation path/to/document.pdf

# Extract citation from a URL
citation https://example.com/article

# With options
citation input --output-dir my_citations --verbose
```

Options:
- `--output-dir`, `-o`: Output directory for citation files (default: citations)
- `--verbose`, `-v`: Enable verbose logging
- `--lang`, `-l`: Language for OCR (default: eng+chi_sim)
- `--type`, `-t`: Manually specify document type (book, thesis, journal, bookchapter)

### Python API

```python
from citation import CitationExtractor

extractor = CitationExtractor()

# Auto-detect input type (output_dir and doc_type_override are optional)
citation_info = extractor.extract_citation("document.pdf", output_dir="citations", doc_type_override="book")
citation_info = extractor.extract_citation("https://example.com/article")

# Or use specific methods
citation_info = extractor.extract_from_pdf("document.pdf")
citation_info = extractor.extract_from_url("https://example.com/article")
```

## Architecture

The system is organized into modular components:

- **`main.py`**: Core extraction logic and workflow orchestration
- **`cli.py`**: Command-line interface with auto-detection
- **`model.py`**: DSPy-based LLM integration for citation extraction
- **`utils.py`**: Common utility functions for file/URL handling
- **`tests/`**: Comprehensive test suite

## Workflow

The extraction follows a multi-step process:

### For PDFs:
1. **PDF Analysis**: Determine document type based on page count.
2. **Metadata Extraction**: Use **PyMuPDF (fitz)** for fast title and metadata extraction.
3. **Scholarly Search**: Query Google Scholar for additional information (if `scholarly` is installed).
4. **OCR Processing**: Make PDF searchable using `ocrmypdf` if needed.
5. **LLM Extraction**: Use DSPy with Ollama/Qwen3 for final extraction if metadata is insufficient.
6. **Output**: Save as YAML and JSON files.

### For URLs:
1. **URL Type Detection**: Determine if text-based or media content.
2. **Content Extraction**: Use a multi-layered approach with `trafilatura`, `newspaper3k`, and `BeautifulSoup` for robust content extraction.
3. **Output**: Save as YAML and JSON files.

## Requirements

- Python 3.12+
- Ollama with Qwen3 model running locally
- **PyMuPDF** (`fitz`) for PDF metadata extraction
- **OCRmyPDF** for PDF processing
- **trafilatura**, **newspaper3k**, **BeautifulSoup4** for URL content extraction
- **scholarly** (optional) for enhanced metadata from Google Scholar

## Testing

Run tests with:
```bash
pytest citation/tests/
```

Add your PDF examples to the `examples/` directory for testing.

## Key Improvements

- **Auto-detection**: No need to specify `--pdf` or `--url` flags.
- **Modular design**: Separated concerns into utils, model, and main modules.
- **Better metadata extraction**: Uses **PyMuPDF (fitz)** for robust and fast PDF metadata extraction.
- **Robust error handling**: Graceful fallbacks when dependencies are unavailable.
- **Comprehensive testing**: Full test coverage for all functionality.
