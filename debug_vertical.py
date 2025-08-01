import fitz  # PyMuPDF
from paddleocr import PaddleOCR
import logging
import os
import sys

# --- Configuration ---
# Use the path from your command, but adjusted to be relative to the script
# Or provide the full absolute path.
PDF_PATH = "../../Downloads/Phd/1Turfan-吐鲁番/K14dagu1-4/01.pdf"
PAGE_NUMBER = 5  # The first page in your range (5-6)
OUTPUT_IMAGE_PATH = "debug_page.png"

# --- Setup ---
logging.basicConfig(level=logging.INFO)
# This is needed to avoid a setuptools error with paddle
try:
    import setuptools
except ImportError:
    print("Installing setuptools for paddleocr...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "setuptools"])

# Initialize PaddleOCR
print("Initializing PaddleOCR (this may take a moment)...")
try:
    ocr_engine = PaddleOCR(use_angle_cls=True, lang='ch')
    print("PaddleOCR initialized.")
except Exception as e:
    print(f"Failed to initialize PaddleOCR: {e}")
    sys.exit(1)


# --- Main Logic ---
def debug_orientation(pdf_path, page_num_1_based):
    """
    Debugs the orientation detection for a single PDF page.
    """
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF file not found at '{os.path.abspath(pdf_path)}'")
        return

    try:
        doc = fitz.open(pdf_path)
        page_num_0_based = page_num_1_based - 1

        if not (0 <= page_num_0_based < doc.page_count):
            print(f"ERROR: Invalid page number {page_num_1_based}. PDF has {doc.page_count} pages.")
            return

        print(f"\n--- Analyzing Page {page_num_1_based} from {pdf_path} ---")
        page = doc[page_num_0_based]

        # 1. Save the page as an image for visual inspection
        pix = page.get_pixmap()
        pix.save(OUTPUT_IMAGE_PATH)
        print(f"Saved page {page_num_1_based} as '{OUTPUT_IMAGE_PATH}' for you to inspect.")

        # 2. Run OCR detection
        img_bytes = pix.tobytes("png")
        print("Running PaddleOCR detection...")
        result = ocr_engine.ocr(img_bytes)
        print("Detection complete.")

        # 3. Analyze and print results
        if not (result and result[0]):
            print("\n--- OCR Result ---")
            print("PaddleOCR did not detect any text on this page.")
            print("This is likely the reason for the misclassification.")
            return

        print("\n--- OCR Result Details ---")
        vertical_count = 0
        horizontal_count = 0
        for i, line in enumerate(result[0]):
            points = line[0]
            text = line[1][0]
            confidence = line[1][1]

            # Use min/max of all points to get the axis-aligned bounding box
            min_x = min(p[0] for p in points)
            max_x = max(p[0] for p in points)
            min_y = min(p[1] for p in points)
            max_y = max(p[1] for p in points)

            height = max_y - min_y
            width = max_x - min_x

            orientation = "Vertical" if height > width else "Horizontal"
            if height > width:
                vertical_count += 1
            else:
                horizontal_count += 1

            print(f"Box {i+1}: Text='{text}', Confidence={confidence:.2f}, Height={height:.1f}, Width={width:.1f} -> Detected as {orientation}")
            print(f"  - Coords: {points}")


        print("\n--- Final Calculation ---")
        print(f"Vertical Boxes: {vertical_count}")
        print(f"Horizontal Boxes: {horizontal_count}")
        final_decision = "VERTICAL" if vertical_count > horizontal_count else "HORIZONTAL"
        print(f"Final Decision: {final_decision}")

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
    finally:
        if 'doc' in locals() and doc:
            doc.close()

if __name__ == "__main__":
    debug_orientation(PDF_PATH, PAGE_NUMBER)
