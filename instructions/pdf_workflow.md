# PDF Citation Extraction Workflow - Detailed Process

## Overview
The system processes PDFs through 8 main steps with three different text direction modes (horizontal, vertical, auto).

## Step-by-Step Workflow

### **Step 1: PDF Structure Analysis**
```
📄 Starting PDF citation extraction...
🔍 Step 1: Analyzing original PDF structure...
```
- Opens PDF with PyMuPDF (fitz)
- Counts total pages (`num_pages`)
- Extracts basic metadata
- Gets filename for reference

### **Step 2: Document Type Pre-filtering**
```
📊 Step 2: Document type pre-filtering from page count (X pages)...
```
**Logic:**
- `num_pages >= 70`: → Allowed types: `["book", "thesis"]`, Default: `"book"`
- `num_pages < 70`: → Allowed types: `["journal", "bookchapter"]`, Default: `"journal"`

### **Step 3: Page Range Subset Creation**
```
✂️ Step 3: Creating temporary PDF from page range 'X-Y, -Z'...
```
- Parses page range (e.g., "1-5, -3" = pages 1-5 and last 3 pages)
- Creates temporary PDF containing only specified pages
- Stores as `temp_pdf_path`

### **Step 4: Text Direction Processing** ⭐

#### **4A: HORIZONTAL Mode**
```
📋 Step 4: Processing in HORIZONTAL mode...
🔍 Horizontal mode: Checking if PDF is searchable...
```
1. **Searchability Check:**
   - Tests first 3 pages for existing text
   - If searchable: Use temp PDF directly
   - If scanned: Perform enhanced language detection + OCR

2. **Text Extraction:**
   - Skip cover pages (using `is_cover_page()`)
   - Extract text from remaining pages
   - Concatenate with `\n\n` separators

#### **4B: VERTICAL Mode**
```
📋 Step 4: Processing in VERTICAL mode...
🔍 Vertical mode: Per-page analysis and mixed processing...
```
1. **Per-Page Layout Analysis:**
   - Analyze each page individually
   - Use `is_vertical_from_layout()` to determine layout
   - Classify as: `"vertical"`, `"horizontal"`, or `"blank"`

2. **Mixed Processing Strategy:**
   - **Vertical pages**: Use PaddleOCR with vertical text detection
   - **Horizontal pages**: Use vertical OCR languages for consistency
   - **Blank pages**: Skip entirely

3. **Text Extraction:**
   - Process each page based on classification
   - Add `\n\n---\n\n` separators between pages

#### **4C: AUTO Mode**
```
📋 Step 4: Processing in AUTO mode (first page analysis)...
🔍 Auto mode: Analyzing first page to determine mode...
```
1. **First Page Analysis:**
   - Analyze only the first content page (skip blanks/covers)
   - Use `is_vertical_from_layout()` for layout detection

2. **Mode Switching:**
   - **First page is vertical** → Switch to VERTICAL mode
   - **First page is horizontal** → Switch to HORIZONTAL mode
   - **Detection fails** → Default to HORIZONTAL mode

### **Step 5: Document Type Determination**
```
🔍 Step 5: Determining document type with pre-filtering...
📋 Determined document type: [TYPE]
```
- Uses `determine_document_type()` with full analysis
- Applies pre-filtering from Step 2
- Falls back to default if detected type not allowed

### **Step 6: Specialized Page Number Extraction** (Conditional)
```
🤖 Step 6: Specialized page number extraction for [journal/bookchapter]...
📄 Page numbers: X-Y
```
**Only for journal/bookchapter documents:**
- Extracts specific page ranges cited
- Uses specialized LLM prompts
- Adds to citation metadata

### **Step 7: LLM Citation Extraction** ⭐

#### **7A: Vertical Citation LLM** (for vertical/auto with vertical detection)
```
📋 Using Vertical Citation LLM for Traditional Chinese/Japanese text
```
- Uses `VerticalCitationLLM` class
- Enhanced DSPy signature for CJK text
- Specialized author parsing (dynasty + role indicators)  
- Title vs series distinction validation
- Chinese/Japanese year conversion
- Returns structured author info: `[{'family': '朱', 'given': '熹', 'dynasty': '宋', 'role': '撰'}]`

#### **7B: Regular Citation LLM** (for horizontal mode)
```
📋 Using Regular Citation LLM
```
- Uses standard `CitationLLM` class
- General citation extraction
- Western-style author parsing

### **Step 8: CSL JSON Conversion & Save**
```
💾 Step 8: Converting to CSL JSON and saving...
✅ Citation extraction completed successfully!
```
1. **Format Conversion:**
   - Converts internal format to CSL-JSON standard
   - Handles author formatting (supports both string and structured formats)
   - Maps document types to CSL types

2. **File Output:**
   - Saves citation as markdown file
   - Uses title/author for filename generation
   - Creates in specified output directory

## Text Direction Mode Comparison

| Mode | First Page Analysis | Per-Page Analysis | OCR Strategy | Use Case |
|------|-------------------|------------------|--------------|----------|
| **horizontal** | ❌ | ❌ | Standard multilingual | Western documents, mixed content |
| **vertical** | ❌ | ✅ | PaddleOCR + vertical languages | Traditional Chinese/Japanese books |
| **auto** | ✅ | Conditional | Mixed based on detection | Unknown document orientation |

## Key Features

### **Cover Page Detection**
- Automatically skips copyright pages, title pages
- Uses content analysis and layout patterns
- Configurable in horizontal mode

### **Mixed Layout Handling**
- Vertical mode can handle horizontal pages within vertical documents
- Auto mode switches based on first content page
- Maintains processing consistency

### **Enhanced Author Parsing** (Vertical Mode)
- Extracts dynasty information: `【宋】`
- Separates family/given names: `朱熹`
- Identifies roles: `撰`, `著`, `注`
- Structured output format

### **Language Detection**
- Enhanced OCR language detection
- Vertical-specific language codes: `chi_tra_vert+jpn_vert`
- Fallback strategies for detection failures

### **Cleanup & Error Handling**
- Automatic temporary file cleanup
- Graceful fallbacks for each step
- Detailed logging and progress indicators

## File Flow

```
Input PDF
    ↓
Temporary Subset PDF (pages from range)
    ↓
Searchable PDF (if OCR needed)
    ↓
Accumulated Text
    ↓
Citation Metadata
    ↓
CSL JSON
    ↓
Output Markdown File
```

## Command Examples

### Basic Usage
```bash
python -m citation.main input.pdf --output-dir citations/
```

### Vertical Traditional Chinese/Japanese Documents
```bash
python -m citation.main input.pdf --text-direction vertical --output-dir citations/
```

### Auto-Detection Mode
```bash
python -m citation.main input.pdf --text-direction auto --page-range "2-10, -3" --output-dir citations/
```

### Horizontal Mode with Specific Page Range
```bash
python -m citation.main input.pdf --text-direction horizontal --page-range "1-5" --output-dir citations/
```

## Expected Output Format

### Vertical Citation (Traditional Chinese/Japanese)
```
Type: book
Author: [{'family': '朱', 'given': '熹', 'literal': '【宋】朱熹撰', 'suffix': '撰'}]
Issued: {'date-parts': [[1944]]}
Title: 四書章句集注
Publisher: 中華書局
Volume: 第一輯
Series: 新編諸子集成
```

### Horizontal Citation (Western Format)
```
Type: journal
Author: [{'family': 'Smith', 'given': 'John'}]
Issued: {'date-parts': [[2023]]}
Title: Research Article Title
Container-title: Journal Name
Volume: 15
Issue: 3
Page: 123-145
```

