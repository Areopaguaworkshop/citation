# Citation Extractor

A tool to extract citations from PDF files and URLs in Chicago Author-Date style.

## Features

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

Extract citation from a PDF file:
```bash
citation --pdf path/to/document.pdf
```

Extract citation from a URL:
```bash
citation --url https://example.com/article
```

Options:
- `--output-dir`, `-o`: Output directory for citation files (default: citations)
- `--verbose`, `-v`: Enable verbose logging
- `--lang`, `-l`: Language for OCR (default: eng+chi_sim)

### Python API

```python
from citation import CitationExtractor

extractor = CitationExtractor()

# Extract from PDF
citation_info = extractor.extract_from_pdf("document.pdf")

# Extract from URL
citation_info = extractor.extract_from_url("https://example.com/article")
```

## Workflow

The extraction follows a multi-step process:

1. **PDF Analysis**: Determine document type based on page count
2. **Metadata Extraction**: Use refextract for initial metadata
3. **Scholarly Search**: Query Google Scholar for additional information
4. **OCR Processing**: Make PDF searchable if needed
5. **LLM Extraction**: Use DSPy with Ollama/Qwen3 for final extraction
6. **Output**: Save as YAML and JSON files

## Requirements

- Python 3.12+
- Ollama with Qwen3 model running locally
- OCRmyPDF for PDF processing
- Anystyle for URL citation extraction

## Testing

Run tests with:
```bash
pytest citation/tests/
```

Add your PDF examples to the `examples/` directory for testing.
