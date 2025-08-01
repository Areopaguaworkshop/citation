import logging
import fitz  # PyMuPDF 
import subprocess
import tempfile
import os
from langdetect import detect, LangDetectException
from typing import Optional


def map_lang_to_tesseract(lang_code: str) -> str:
    """Maps a language code from langdetect to a Tesseract language code."""
    mapping = {
        "zh-cn": "chi_sim",
        "zh": "chi_sim",  # Default Chinese to simplified
        "zh-tw": "chi_tra", 
        "ja": "jpn",
        "ko": "kor",
        "de": "deu",
        "fr": "fra",
        "es": "spa",
        "ru": "rus",
        "ar": "ara",
        "hi": "hin",
        "it": "ita",
        "pt": "por",
    }
    return mapping.get(lang_code, lang_code)


def detect_language_from_scanned_pdf(pdf_path: str) -> Optional[str]:
    """Detect language from a scanned (non-searchable) PDF by OCRing one page."""
    print("🔍 Detecting language from scanned PDF...")
    try:
        # Create a temporary single page for language detection
        doc = fitz.open(pdf_path)
        if doc.page_count == 0:
            doc.close()
            return None
            
        # Try first few pages to find one with substantial content
        temp_single_page = None
        detected_lang = None
        
        # Enhanced language list: English + Simplified Chinese (priority) + French + German + Russian
        detection_languages = "eng+chi_sim+fra+deu+rus+chi_tra+jpn"
        
        for page_num in range(min(3, doc.page_count)):
            try:
                # Create single page PDF
                temp_single_page = f"/tmp/lang_detect_page_{page_num}.pdf"
                single_doc = fitz.open()
                single_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                single_doc.save(temp_single_page)
                single_doc.close()
                
                # Quick OCR with enhanced languages for detection
                temp_ocr = f"/tmp/lang_detect_ocr_{page_num}.pdf"
                cmd = ["ocrmypdf", "--force-ocr", "-l", detection_languages, 
                       temp_single_page, temp_ocr]
                
                print(f"📄 Testing page {page_num + 1} for language detection...")
                process = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if process.returncode == 0:
                    # Extract text and detect language
                    ocr_doc = fitz.open(temp_ocr)
                    text = ocr_doc[0].get_text().strip()
                    ocr_doc.close()
                    
                    if text and len(text) > 50:  # Need substantial text
                        detected_lang_code = detect(text)
                        tesseract_lang = map_lang_to_tesseract(detected_lang_code)
                        
                        # Priority handling for Chinese
                        if detected_lang_code.startswith('zh'):
                            # Analyze characters to distinguish Traditional vs Simplified
                            traditional_chars = set('繁體中文傳統字形華語國語臺灣香港澳門')
                            simplified_chars = set('简体中文传统字形华语国语台湾香港澳门')
                            
                            traditional_count = sum(1 for char in text if char in traditional_chars)
                            simplified_count = sum(1 for char in text if char in simplified_chars)
                            
                            if traditional_count > simplified_count:
                                tesseract_lang = "chi_tra"
                                print(f"✅ Chinese detected as Traditional: {detected_lang_code} → {tesseract_lang}")
                            else:
                                tesseract_lang = "chi_sim"
                                print(f"✅ Chinese detected as Simplified: {detected_lang_code} → {tesseract_lang}")
                        else:
                            print(f"✅ Language detected: {detected_lang_code} → {tesseract_lang}")
                        
                        detected_lang = tesseract_lang
                        break
                    
                    os.remove(temp_ocr)
                    
                # Cleanup temp files
                os.remove(temp_single_page)
                
            except Exception as e:
                print(f"⚠️ Page {page_num + 1} detection failed: {e}")
                if temp_single_page and os.path.exists(temp_single_page):
                    os.remove(temp_single_page)
                continue
        
        doc.close()
        return detected_lang

    except Exception as e:
        print(f"❌ Error during language detection: {e}")
        return None


def get_ocr_language_string(detected_lang: Optional[str] = None) -> str:
    """Get OCR language string with English and Simplified Chinese as priority base."""
    base_langs = "eng+chi_sim"  # Priority: English + Simplified Chinese
    
    if detected_lang and detected_lang not in ["eng", "chi_sim"]:
        return f"{base_langs}+{detected_lang}"
    else:
        return base_langs


def get_vertical_ocr_languages() -> str:
    """Get OCR languages for vertical text processing."""
    return "chi_tra_vert+jpn_vert"


def get_auto_mode_horizontal_ocr_languages() -> str:
    """Get OCR languages for horizontal pages in auto mode."""
    return "chi_tra+jpn"
