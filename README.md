<p align="center">
  <img src="./Citation-Extractor-logo.PNG" alt="Citation Extractor Logo" width="150">
</p>

<h1 align="center">🔍 Citation Extractor</h1>

<p align="center">
  <strong>We're living in an era where AI can write beautifully, but can't cite properly.</strong>
  <br>
  <em>Because every claim deserves a source, and every source deserves proper citation.</em>
</p>

<p align="center">
  <a href="#--why-this-matters">Why This Matters</a> •
  <a href="#--features">Features</a> •
  <a href="#--quick-start">Quick Start</a> •
  <a href="#--usage">Usage</a> •
  <a href="#--contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT">
  <img src="https://img.shields.io/pypi/v/cite-extractor.svg" alt="PyPI version">
  <img src="https://img.shields.io/pypi/dm/cite-extractor.svg" alt="PyPI downloads">
</p>

---

## 🚨 Why This Matters

**We're living in an era where AI can write beautifully, but can't cite properly.**

Large Language Models (LLMs) like ChatGPT, Claude, and Gemini are incredible at generating human-like text, but they have a **fundamental flaw**: they lack reliable citation mechanisms. When an LLM tells you about a scientific study, historical event, or technical concept, you're left wondering:

- 📚 **Where did this information come from?**
- 🔍 **How can I verify these claims?**
- 📝 **How do I properly cite this in my research?**

This creates a **trust gap** that undermines the reliability of AI-generated content, especially in academic, professional, and research contexts.

**Citation Extractor exists to fill this gap.** 

While LLMs struggle with proper citations, this tool excels at extracting structured, verifiable citation data from any source. It's the missing piece that makes AI-generated content trustworthy and academically sound.

## 🌟 Features

### 🎯 **Universal Source Support**
- **📄 Document Versatility**: Handles `.pdf`, `.docx`, `.djvu`, `.epub`, and more.
- **🌐 Web & Media**: Extracts citations directly from URLs and media files (`.mp4`, `.mp3`).

### 🧠 **AI-Powered Intelligence**
- **Smart Document Classification**: Automatically detects if a source is a book, journal article, thesis, or chapter.
- **Advanced, Multilingual OCR**: Accurately processes scanned documents, including those with **vertical text** layouts (e.g., Chinese, Japanese).
- **Smarter Language Detection**: Intelligently skips blank cover pages to find the first page with text, ensuring the correct language is used for OCR.
- **Automatic OCR Error Correction**: Proactively fixes common OCR mistakes (e.g., `郭庆沙` → `郭庆藩`) before extraction for higher accuracy.
- **Flexible LLM Backend**: Works with Ollama (local) or cloud APIs (Gemini, OpenAI).

### 📚 **Research-Grade Output**
- **CSL-JSON Standard**: Compatible with Zotero, Mendeley, and all major reference managers.
- **Multiple Citation Styles**: Instantly format in Chicago, APA, MLA, or any other CSL style.
- **Rich, Structured Metadata**: Captures author, title, date, DOI, ISBN, and even complex author details like historical dynasties (`[清]`).

### ⚡ **Optimized Performance**
- **Smart Page Selection**: Processes only the most relevant pages for speed.
- **Iterative Extraction**: Stops as soon as all essential citation fields are found.
- **Batch Processing**: Handle multiple documents efficiently.

## 🚀 Quick Start

### Installation

```bash
pip install cite-extractor
```

### System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr mediainfo

# macOS
brew install tesseract mediainfo

# For local LLM support (optional)
# Install Ollama: https://ollama.ai/
```

### First Citation

```bash
# Extract from a PDF
citation "path/to/research-paper.pdf"

# Extract from a URL
citation "https://www.nature.com/articles/s41586-023-06627-7"

# Extract from a document with vertical text
citation "path/to/vertical-text-document.pdf" --text-direction vertical
```

## 📖 Usage

### Command Line Interface

```bash
# Basic usage
citation "document.pdf"

# Specify document type
citation "thesis.pdf" --type thesis

# Use different LLM
citation "paper.pdf" --llm gemini/gemini-1.5-flash

# Custom output directory
citation "book.pdf" --output-dir ./citations

# Specific page range for large documents
citation "book.pdf" --page-range "1-5, -3"

# Different citation style
citation "article.pdf" --citation-style apa
```

### Python API

```python
from citation.main import CitationExtractor
from citation.citation_style import format_bibliography

# Initialize with your preferred LLM
extractor = CitationExtractor(llm_model="ollama/qwen3")

# Extract citation data
csl_data = extractor.extract_citation("research-paper.pdf")

if csl_data:
    # Format as bibliography
    bibliography, in_text = format_bibliography([csl_data], "chicago-author-date")
    
    print("📚 Bibliography:")
    print(bibliography)
    
    print("\n📝 In-text citation:")
    print(in_text)
```

### Advanced Configuration

```bash
# For non-English documents, let the tool auto-detect the language
citation "chinese-paper.pdf" --lang auto

# Or specify manually
citation "another-paper.pdf" --lang chi_sim+eng

# Verbose output for debugging
citation "document.pdf" --verbose
```

## 🤝 Contributing

**We're thrilled to have you join this mission!** 🎉

This project addresses a fundamental need in our AI-driven world, and we believe it can make a real difference in how we handle information credibility. Whether you're a developer, researcher, or just someone who cares about proper attribution, there's a place for you here.

### 🚀 How to Contribute

1. **🐛 Report Issues**: Found a bug or have a feature request?
2. **💡 Suggest Improvements**: Ideas for better citation extraction?
3. **🔧 Submit Code**: Bug fixes, new features, or optimizations
4. **📚 Improve Documentation**: Help others understand and use the tool
5. **🌍 Add Language Support**: Extend OCR and extraction to new languages
6. **🎨 Citation Styles**: Add support for more academic citation styles

### 💻 Development Setup

```bash
git clone https://github.com/your-username/citation-extractor.git
cd citation-extractor

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
```

## 🏆 Acknowledgments

This project stands on the shoulders of giants:
- **DSPy**: For flexible LLM integration
- **Tesseract**: For OCR capabilities
- **citeproc-py**: For citation formatting
- **The Open Source Community**: For making tools like this possible

## 📄 License

MIT License - feel free to use this in your projects, commercial or otherwise.

---

<p align="center">
  <strong>Made with ❤️ for the research community</strong>
  <br>
  <em>Because every claim deserves a source, and every source deserves respect.</em>
</p>

<p align="center">
  ⭐ <strong>Star this repo if you find it useful!</strong> ⭐
</p>