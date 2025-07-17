<p align="center">
  <img src="https://raw.githubusercontent.com/jgm/citeproc/master/img/citeproc-logo.png" alt="Citeproc Logo" width="150">
</p>

<h1 align="center">Citation Extractor</h1>

<p align="center">
  <strong>Effortlessly extract structured citation data from any source.</strong>
  <br>
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT">
  <a href="https://github.com/your-username/citation/issues">
    <img src="https://img.shields.io/github/issues/your-username/citation" alt="GitHub issues">
  </a>
  <a href="https://github.com/your-username/citation/pulls">
    <img src="https://img.shields.io/github/issues-pr/your-username/citation" alt="GitHub pull requests">
  </a>
</p>

---

**Citation Extractor** is a powerful, AI-driven tool designed to automatically pull accurate, structured citation information from a wide variety of sources, including academic papers, websites, and even local media files. By leveraging Large Language Models (LLMs) and intelligent document analysis, it saves you hours of manual work and ensures your references are perfectly formatted.

Whether you're a researcher, student, or developer, this tool provides a seamless bridge from raw content to clean, CSL-JSON formatted citations.

## Features

- **Universal Input Support**:
  - **PDFs**: Automatically determines if the document is a book, thesis, journal article, or book chapter.
  - **Web URLs**: Intelligently extracts metadata from articles and webpages.
  - **Media Files**: Pulls metadata from local video and audio files (`.mp4`, `.mp3`, etc.).

- **Intelligent PDF Processing**:
  - **Smart OCR**: Uses `ocrmypdf` to make scanned PDFs searchable.
  - **Efficient Analysis**: Processes only the most relevant pages (e.g., first 5, last 3) to speed up extraction without sacrificing accuracy.
  - **Automatic Type Detection**: Accurately classifies your documents to apply the correct extraction logic.

- **AI-Powered Extraction**:
  - **Flexible LLM Backend**: Powered by **DSPy**, it supports various LLMs including local models via **Ollama** (`qwen3`, `llama3`) and powerful cloud APIs like **Google Gemini**.
  - **Iterative Deep-Scan**: For complex documents, the tool iteratively scans pages and accumulates text, stopping as soon as all essential citation fields are found.
  - **Web Content Fallback**: Uses `crawl4ai` to deeply analyze web pages when initial metadata extraction is insufficient.

- **High-Quality Formatted Output**:
  - **CSL-JSON Standard**: Generates clean, standard-compliant CSL-JSON files, ready for any reference manager.
  - **Styled Bibliographies**: Instantly format citations in different styles (e.g., Chicago, APA) using the `citeproc-py` library.

- **Developer-Friendly**:
  - **Robust CLI**: A powerful command-line interface with comprehensive options for power users.
  - **Simple Python API**: Easily integrate citation extraction into your own Python applications.

## Installation

### Prerequisites

Make sure you have the following dependencies installed on your system:

- **Python 3.12+**
- **Tesseract OCR**: For making PDFs searchable.
- **MediaInfo**: For extracting metadata from media files.
- **Ollama** (Optional): For running local LLMs.

**On Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr mediainfo
# Install Ollama by following the official instructions at https://ollama.ai/
```

**On macOS:**
```bash
brew install tesseract mediainfo ollama
```

### Project Setup

This project uses [Rye](https://rye-up.com/) for streamlined dependency and environment management.

1.  **Install Rye:**
    ```bash
    curl -sSf https://rye-up.com/get | bash
    ```

2.  **Sync Dependencies:**
    Clone the repository and run `rye sync` to install all required Python packages in a virtual environment.
    ```bash
    git clone https://github.com/your-username/citation.git
    cd citation
    rye sync
    ```

## Usage

### From the Command Line

The CLI automatically detects the input type (PDF, URL, or media file).

```bash
# Extract from a PDF file
rye run python -m citation.cli "path/to/your/document.pdf"

# Extract from a website URL
rye run python -m citation.cli "https://www.nature.com/articles/s41586-023-06627-7"

# Extract from a local video file
rye run python -m citation.cli "path/to/your/lecture.mp4"
```

#### Key CLI Options:

| Flag                 | Alias | Description                                                 | Default                            |
| -------------------- | ----- | ----------------------------------------------------------- | ---------------------------------- |
| `--output-dir`       | `-o`  | Directory to save citation files.                           | `example/`                         |
| `--type`             | `-t`  | Override automatic document type detection.                 | `auto`                             |
| `--page-range`       | `-p`  | Page range for PDF processing (e.g., "1-5, -3").            | `"1-5, -3"`                        |
| `--lang`             | `-l`  | Language for OCR.                                           | `eng+chi_sim+chi_tra`              |
| `--llm`              |       | LLM to use (e.g., `ollama/qwen3`, `gemini/gemini-1.5-flash`). | `ollama/qwen3`                     |
| `--citation-style`   | `-cs` | CSL style for formatted output.                             | `chicago-author-date`              |
| `--verbose`          | `-v`  | Enable detailed logging.                                    | `False`                            |

### As a Python Library

Integrate citation extraction directly into your projects with the `CitationExtractor`.

```python
from citation.main import CitationExtractor
from citation.citation_style import format_bibliography

# Initialize the extractor with your chosen LLM
extractor = CitationExtractor(llm_model="ollama/qwen3")

# Extract citation data from a source
csl_data = extractor.extract_citation("path/to/document.pdf")

if csl_data:
    # Format the bibliography
    bibliography, in_text = format_bibliography([csl_data], "chicago-author-date")
    
    print("--- Formatted Bibliography ---")
    print(bibliography)
    
    print("\n--- In-Text Citation ---")
    print(in_text)
```

## Testing

To ensure everything is working correctly, run the test suite using `pytest`:

```bash
rye run pytest
```

## Contributing

Contributions are welcome! Whether it's a bug report, feature request, or a pull request, your input is valued. Please feel free to open an issue or submit a PR.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.