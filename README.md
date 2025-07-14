# Citation Extractor

A powerful tool to extract citations from PDF files, URLs, and local media files in Chicago Author-Date style using advanced LLM technology.

## Features

- **🔍 Auto-detection**: Automatically detects input type (PDF, URL, video/audio file)
- **📄 PDF Support**: Extract citations from books, theses, journals, and book chapters
- **🌐 URL Support**: Extract citations from web articles and media content
- **🎵 Media Support**: Extract citations from local video and audio files
- **🌍 Multi-language**: Support for English and Chinese content
- **🤖 LLM-Powered**: Uses DSPy with flexible LLM model selection (Ollama, Gemini)
- **📊 Multiple Formats**: Output in both YAML and JSON formats
- **🔄 Robust Workflow**: Multi-step extraction with intelligent fallbacks
- **⚡ Fast Processing**: Efficient PyMuPDF-based PDF processing

## Installation

### Prerequisites
- Python 3.12+
- [Ollama](https://ollama.ai) with a compatible model (e.g., `qwen3`, `llama3`)
- OCRmyPDF for PDF text extraction
- MediaInfo for media file processing

### Install using Rye (Recommended)

```bash
rye sync
```

### Install using pip

```bash
pip install -e .
```

## Quick Start

### Command Line Interface

```bash
# Extract citation from a PDF file
citation path/to/document.pdf

# Extract citation from a URL
citation https://example.com/article

# Extract citation from a local video file
citation path/to/video.mp4

# Use different LLM models
citation --llm ollama/llama3 document.pdf
citation --llm gemini/gemini-1.5-flash document.pdf

# With all options
citation --llm ollama/qwen3 --type book --output-dir my_citations --verbose document.pdf
```

### Available Options

- `--llm`: LLM model to use (default: `ollama/qwen3`)
  - Ollama: `ollama/qwen3`, `ollama/llama3`, `ollama/mixtral`
  - Gemini: `gemini/gemini-1.5-flash`, `gemini/gemini-2.0-flash-exp`
- `--output-dir`, `-o`: Output directory for citation files (default: `citations`)
- `--verbose`, `-v`: Enable verbose logging
- `--lang`, `-l`: Language for OCR (default: `eng+chi_sim`)
- `--type`, `-t`: Manually specify document type (book, thesis, journal, bookchapter)

### Python API

```python
from citation import CitationExtractor

extractor = CitationExtractor()

# Auto-detect input type
citation_info = extractor.extract_citation("document.pdf")
citation_info = extractor.extract_citation("https://example.com/article")
citation_info = extractor.extract_citation("my_video.mp4")

# Or use specific methods
citation_info = extractor.extract_from_pdf("document.pdf")
citation_info = extractor.extract_from_url("https://example.com/article")
citation_info = extractor.extract_from_media_file("my_audio.mp3")
```

## Architecture

The system is organized into modular components:

- **`main.py`**: Core extraction logic and workflow orchestration.
- **`cli.py`**: Command-line interface with auto-detection.
- **`model.py`**: DSPy-based LLM integration for citation extraction from PDFs.
- **`utils.py`**: Common utility functions for file/URL handling and type detection.
- **`tests/`**: Comprehensive test suite.

## Workflow

The extraction follows an intelligent multi-step process based on input type:

### 📄 PDF Processing Workflow

1. **PDF Structure Analysis**: Analyze page count and extract basic metadata
2. **Document Type Detection**: Determine if book (>70 pages), thesis, journal, or book chapter
3. **OCR Processing**: Make PDF searchable using OCRmyPDF if needed
   - Books/Thesis: OCR first 10 pages + last 2 pages for efficiency
   - Articles: OCR all pages for accuracy
4. **Text Extraction**: Extract relevant text using PyMuPDF
5. **LLM-Based Extraction**: Use DSPy with configurable LLM models
   - **Books**: Focus on cover and copyright pages (first 5 pages)
   - **Thesis**: Similar to books but detect thesis-specific terms
   - **Journal**: Extract from first page headers/footers
   - **Book Chapter**: Extract chapter info and parent book details
6. **Post-processing**: Add page numbers and validate results
7. **Output**: Save as YAML and JSON files

### 🌐 URL Processing Workflow

1. **URL Type Detection**: Determine if text-based or media content
2. **Multi-layered Content Extraction**: 
   - **Primary**: Trafilatura for structured content
   - **Fallback**: Newspaper3k for news articles
   - **Final**: BeautifulSoup for HTML meta tags
3. **Publisher Detection**: Extract from domain if not found
4. **Date Processing**: Add access date and parse publication date
5. **Output**: Save as YAML and JSON files

### 🎵 Media File Processing Workflow

1. **Metadata Extraction**: Use PyMediaInfo to extract technical metadata
2. **Title Processing**: Use embedded title or derive from filename
3. **Duration Formatting**: Convert to human-readable format
4. **Author/Publisher**: Extract from metadata or mark as missing
5. **Output**: Save as YAML and JSON files

## LLM Model Support

The system supports multiple LLM providers through DSPy:

### Ollama (Local Models)
- **Default**: `ollama/qwen3`
- **Supported**: `ollama/llama3`, `ollama/mixtral`, `ollama/codellama`
- **Requirements**: Ollama running on `localhost:11434`

### Google Gemini (API Models)
- **Supported**: `gemini/gemini-1.5-flash`, `gemini/gemini-2.0-flash-exp`
- **Requirements**: Valid Gemini API credentials

### Configuration
```python
# Use different models
extractor = CitationExtractor(llm_model="ollama/llama3")
extractor = CitationExtractor(llm_model="gemini/gemini-1.5-flash")
```

## System Requirements

### Core Dependencies
- **Python 3.12+** (Required)
- **PyMuPDF** (`fitz`) - PDF processing and metadata extraction
- **OCRmyPDF** - PDF text recognition and searchability
- **DSPy** - LLM integration framework
- **PyMediaInfo** - Media file metadata extraction

### Web Scraping Dependencies
- **Trafilatura** - Primary content extraction
- **Newspaper3k** - News article processing
- **BeautifulSoup4** - HTML parsing fallback
- **Requests** - HTTP client

### LLM Dependencies
- **Ollama** (for local models) - Install from [ollama.ai](https://ollama.ai)
- **Google AI SDK** (for Gemini models) - Configured via environment variables

### System Tools
- **Tesseract OCR** - Required by OCRmyPDF
- **MediaInfo** - Required by PyMediaInfo

## Development and Testing

### Running Tests
```bash
# Run all tests
pytest citation/tests/

# Run with coverage
pytest --cov=citation citation/tests/

# Run specific test file
pytest citation/tests/test_citation.py
```

### Project Structure
```
citation/
├── citation/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # Core extraction logic
│   ├── cli.py               # Command-line interface
│   ├── model.py             # DSPy LLM integration
│   ├── llm.py               # LLM model configuration
│   ├── utils.py             # Utility functions
│   └── tests/               # Test suite
├── citations/               # Default output directory
├── README.md                # This file
├── pyproject.toml           # Project configuration
└── LLM_USAGE_EXAMPLES.md    # LLM usage examples
```

## Output Format

Citations are saved in both YAML and JSON formats following Chicago Author-Date style:

### PDF Book Example
```yaml
title: "The Great Gatsby"
author: "Fitzgerald, F. Scott"
publisher: "Charles Scribner's Sons"
year: "1925"
location: "New York"
isbn: "978-0-7432-7356-5"
```

### URL Article Example
```yaml
title: "Climate Change and Its Effects"
author: "Smith, John"
url: "https://example.com/article"
date_accessed: "2024-01-15"
publisher: "Science Daily"
date: "2024-01-10"
```

## Troubleshooting

### Common Issues

1. **LLM Provider Error**: Ensure Ollama is running and model is pulled
   ```bash
   ollama pull qwen3
   ollama serve
   ```

2. **OCR Failures**: Install Tesseract OCR
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr
   
   # macOS
   brew install tesseract
   ```

3. **Media File Issues**: Install MediaInfo
   ```bash
   # Ubuntu/Debian
   sudo apt-get install mediainfo
   
   # macOS
   brew install mediainfo
   ```

### Debug Mode
```bash
# Enable verbose logging
citation --verbose document.pdf

# Check LLM configuration
python -c "from citation.llm import get_provider_info; print(get_provider_info())"
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
