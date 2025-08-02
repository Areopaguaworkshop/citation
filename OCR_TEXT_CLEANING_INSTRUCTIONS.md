# OCR Text Cleaning Instructions for Citation Extraction

## Overview
Add a new step (Step 4.5) between text extraction and document type determination to clean and filter OCR/searchable text before LLM processing.

## Step 4.5: OCR Text Cleaning (ocr_text_clean_before_llm.py)

### Input
- Searchable or OCR'd text from Step 4
- Document metadata (page count, text direction, page range)

### Processing Logic

#### 1. Universal Filtering
- **Ignore cover pages with images** (use existing project function)
- **Ignore blank pages** (pages with no text content)

#### 2. Document Size-Based Processing

##### For Documents >= 70 pages (Books/Theses)
- **Content Page Detection**: Look for "Contents" (or equivalent in French, German, Chinese, Japanese, Russian) in first line with big font-size
  - Once detected, remove Contents page and all pages after it
  - This is especially important when page-range includes content pages
- **Keep**: Only pages before Contents page

##### For Documents < 70 pages (Journals/Chapters)  
- **First Page Processing**: 
  - Keep content of first page with big font-size text in lines 2-8
  - This typically contains title, author, abstract - the citation-relevant information
- **Subsequent Pages**:
  - Keep only headers and footers
  - Remove main body content (to focus LLM on citation info only)

#### 3. Text Direction Handling

##### Vertical Text (Chinese, Japanese, etc.)
- **Reading sequence**: Top to bottom, then right to left
- **Header/Footer positions**: 
  - Headers: Right side of pages
  - Footers: Left side of pages

##### Horizontal Text
- **Reading sequence**: Left to right, top to bottom  
- **Header/Footer positions**:
  - Headers: Top of pages
  - Footers: Bottom of pages

### Goal
Provide LLM with only the most relevant text for citation extraction while removing noise and irrelevant content.

### Languages Supported
- English: "Contents", "Table of Contents"
- French: "Sommaire", "Table des matières"  
- German: "Inhalt", "Inhaltsverzeichnis"
- Chinese: "目录", "目次", "內容"
- Japanese: "目次", "もくじ"
- Russian: "Содержание", "Оглавление"

## Clarifications

1. **Font Size Detection**:
   - Compare with surrounding text, especially following text.
   - Use a relative threshold (1.4x larger).

2. **Page Range Interaction**:
   - If `--page-range` includes the Content page, identify it and remove its content and that of the following page.
   - If not included, skip removal.

3. **Header/Footer Detection**:
   - Try using an OCR tool like ocrmypdf for this.
   - Top 10%/Bottom 10% of page height can be a fallback.

4. **Vertical Text Headers/Footers**:
   - Check if PaddleOCR can identify, use width percentages as fallback.

5. **Content Page Detection Precision**:
   - "Contents" appears in the first line with larger font-size on the page.

6. **Existing Functions**:
   - First look for these before integrating or creating new functionality.

## Updated Plan

### Core Functions

#### Revised Core Steps:

1. **`clean_extracted_text(text: str, num_pages: int, text_direction: str, page_range: str) -> str`**
   - Main function orchestrating the cleaning.

2. **Universal Filtering**:
   - Remove cover pages with images and blank pages.
   - Detect content pages using font size relative to surrounding text.

3. **Specific Processing Based on Document Size**:

   **For Documents ≥ 70 Pages (Books/Theses):**
   - Skip headers/footers, focus on actual content removal if pages include content pages.

   **For Documents < 70 Pages (Journals/Chapters):**
   - Focus on initial pages with larger font-size content.
   - Remove body content after first relevant page.

4. **Text Direction Handling**:
   - Address vertical and horizontal text differently.
   - Ensure accurate header/footer extraction and deletion based on orientation.

5. **Header/Footer Extraction**:
   - Attempt detection with OCR tools like ocrmypdf or PaddleOCR.
   - Use positional heuristics where needed.

### Integration Points
- **Adjust workflow based on document size during processing**
- **Incorporate with existing project functions as needed**


## Final Clarifications

1. **Header/Footer Detection for Vertical Text**:
   - Use PaddleOCR first, then fall back to positional detection (10% of page width).

2. **Content Page Range Detection**:
   - Analyze the extracted text to detect content pages.
   - Remove all content pages and everything after the last one.

3. **Font Size Analysis**:
   - Use existing OCR tools' font size information.
   - Check PaddleOCR library capabilities for font size detection.

4. **Text Structure Preservation**:
   - For ≥70 page documents: Preserve structural information (page numbers, chapter markers).
   - For <70 page documents: Maintain original page structure when keeping headers/footers.

## Implementation Status
Ready to proceed with implementation following these specifications.

