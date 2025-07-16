# Citation Extractor

A powerful, LLM-driven tool to automatically extract citation information from PDFs, web pages, and local media files. It generates structured citation data in JSON and YAML formats and can format bibliographies using various citation styles.

## Features

-   **Multi-Format Support**: Extracts data from PDF documents, web URLs, and local video/audio files.
-   **Intelligent PDF Processing**:
    -   Automatically determines document type (book, thesis, journal article, book chapter).
    -   Uses `OCRmyPDF` to make non-searchable PDFs readable.
    -   Efficiently processes only relevant page ranges (e.g., the first few and last few pages) to speed up extraction.
-   **Advanced Web Scraping**:
    -   Uses a multi-layered approach (Trafilatura, Newspaper3k, BeautifulSoup) for robust content extraction from URLs.
-   **LLM-Powered Extraction**:
    -   Leverages Large Language Models via DSPy for accurate metadata extraction.
    -   Supports multiple LLM backends, including local models with Ollama and cloud APIs like Google Gemini.
-   **Formatted Output**:
    -   Generates CSL-JSON and YAML files.
    -   Prints formatted bibliographies and in-text citations to the console using `citeproc-py`.
-   **User-Friendly**:
    -   Simple command-line interface (CLI).
    -   Verbose mode for detailed logging and debugging.
    -   Python API for integration into other projects.

## How It Works

The tool automatically detects the input type and applies a specialized workflow:

1.  **PDFs**: The PDF is analyzed, and a temporary, smaller PDF containing only the most relevant pages is created. If necessary, OCR is applied. Relevant text is extracted and passed to an LLM, which identifies and extracts citation metadata (title, author, year, etc.) based on the detected document type.
2.  **URLs**: The content of the URL is fetched, and a series of extraction tools are used to pull out metadata. The publisher is inferred from the domain if not explicitly found.
3.  **Media Files**: For local audio or video files, `pymediainfo` is used to extract embedded metadata like title, author, and duration.

The extracted information is then normalized, saved to `.json` and `.yaml` files, and displayed in the console as a formatted citation.

## Installation

### Prerequisites

This tool relies on several external dependencies that must be installed on your system:

-   **Python 3.12+**
-   **Tesseract OCR**: Required by `OCRmyPDF`.
-   **MediaInfo**: Required by `pymediainfo` for media file analysis.
-   **Ollama** (Optional): For running local LLMs.

You can install these on macOS using [Homebrew](https://brew.sh/):

```bash
brew install tesseract mediainfo ollama
```

Or on Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr mediainfo
# Follow instructions on ollama.ai to install Ollama
```

### Application Installation

It is recommended to use [Rye](https://rye-up.com/) for managing Python projects and dependencies.

```bash
rye sync
```

This will create a virtual environment and install all necessary Python packages.

## Usage

### Command-Line Interface

The `citation` command is the primary way to use the tool.

**Basic Usage:**

```bash
# Extract from a PDF
citation /path/to/your/document.pdf

# Extract from a URL
citation "https://www.example.com/article"

# Extract from a local video file
citation /path/to/your/video.mp4
```

**Specifying an LLM:**

You can specify which LLM to use with the `--llm` flag. See [LLM_USAGE_EXAMPLES.md](LLM_USAGE_EXAMPLES.md) for more details.

```bash
# Use a local Llama3 model via Ollama
citation --llm ollama/llama3 /path/to/document.pdf

# Use Google Gemini
export GOOGLE_API_KEY="YOUR_API_KEY"
citation --llm gemini/gemini-1.5-flash /path/to/document.pdf
```

**Other Options:**

-   `-o, --output-dir`: Specify a directory to save citation files (default: `example/`).
-   `-t, --type`: Manually override the document type for PDFs (`book`, `thesis`, `journal`, `bookchapter`).
-   `-p, --page-range`: Specify page range for OCR (e.g., "1-5, -3").
-   `-l, --lang`: Set language for OCR (e.g., `eng+fra`).
-   `-cs, --citation-style`: Choose a CSL style for formatted output (e.g., `chicago-author-date`).
-   `-v, --verbose`: Enable detailed logging.

### Python API

You can also use the `CitationExtractor` class in your own Python scripts.

```python
from citation.main import CitationExtractor

# Initialize the extractor (can specify an LLM model)
extractor = CitationExtractor(llm_model="ollama/qwen3")

# Extract from a PDF
pdf_citation = extractor.extract_from_pdf("path/to/document.pdf")
print(pdf_citation)

# Extract from a URL
url_citation = extractor.extract_from_url("https://example.com/article")
print(url_citation)

# Extract from a media file
media_citation = extractor.extract_from_media_file("path/to/video.mp4")
print(media_citation)
```

## Output Format

For each input, the tool generates a `.json` and a `.yaml` file containing the extracted citation data. The output is structured to be compatible with CSL-JSON format. It also prints a formatted bibliography to the console.

**Example Console Output:**

```
==================================================
FORMATTED BIBLIOGRAPHY (chicago-author-date)
==================================================
Last, First. 2024. “Title of Article.” *Journal Name* 1 (2): 1–10.

==================================================
IN-TEXT CITATION
==================================================
(Last 2024)
```

**Example (`.yaml`):**

```yaml
URL: https://www.example.com
accessed:
  date-parts:
  - - 2025
    - 7
    - 16
id: example
publisher: Example
title: Example Domain
type: webpage
```

## Project Structure

```
.
├── citation/
│   ├── __init__.py
│   ├── cli.py          # Command-line interface logic
│   ├── llm.py          # LLM provider configuration
│   ├── main.py         # Core extraction workflow
│   ├── model.py        # DSPy signatures for LLM extraction
│   ├── utils.py        # Helper functions
│   └── tests/          # Pytest tests
├── example/            # Example output files
├── pyproject.toml      # Project definition and dependencies
└── README.md           # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the MIT License.
