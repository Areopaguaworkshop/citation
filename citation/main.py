import subprocess
import os
import shutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

def ocr_pdf(input_pdf_path, output_pdf_path, lang="eng"):
    """
    Runs ocrmypdf on an input PDF to make it searchable.
    """
    logging.info(
        f"Performing OCR on '{input_pdf_path}' to create '{output_pdf_path}'..."
    )
    try:
        command = [
            "ocrmypdf",
            "--deskew",
            "--force-ocr",
            "-l",
            lang,
            input_pdf_path,
            output_pdf_path,
        ]
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        logging.info(
            f"OCR successful for '{input_pdf_path}'. Output saved to '{output_pdf_path}'"
        )
        return True
    except FileNotFoundError:
        logging.error(
            "ocrmypdf not found. Please ensure it is installed and in your system's PATH."
        )
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f"OCRmyPDF failed for '{input_pdf_path}': {e}")
        logging.error(f"OCRmyPDF stderr:\n{e.stderr}")
        return False
    except Exception as e:
        logging.error(
            f"An unexpected error occurred during OCR for '{input_pdf_path}': {e}"
        )
        return False

def extract_first_page_text(pdf_path):
    """
    Extracts text from the first page of a PDF using pdftotext.
    """
    try:
        result = subprocess.run(
            ["pdftotext", "-l", "1", pdf_path, "-"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        logging.error(
            "pdftotext not found. Please install `poppler-utils` to enable PDF text extraction."
        )
        return None
    except subprocess.CalledProcessError as e:
        logging.error(f"pdftotext failed for '{pdf_path}': {e}")
        return None
    except subprocess.TimeoutExpired:
        logging.error(f"pdftotext timed out for {pdf_path}.")
        return None

def get_pdf_citation_text(input_pdf_path, output_dir="processed_pdfs", lang="eng"):
    """
    Main function to get the text from the first page of a PDF, running OCR if needed.
    """
    if not os.path.exists(input_pdf_path):
        logging.error(f"Input PDF not found: {input_pdf_path}")
        return None

    os.makedirs(output_dir, exist_ok=True)
    temp_searchable_pdf_path = None
    final_pdf_to_process = input_pdf_path

    try:
        # Always run OCR for non-English languages or if the PDF is not searchable
        # to ensure a clean, readable text layer.
        text = extract_first_page_text(input_pdf_path)
        run_ocr = lang != "eng" or not text

        if run_ocr:
            if lang != "eng":
                logging.info(f"Language '{lang}' specified, forcing OCR to ensure correct text layer.")
            else:
                logging.info("PDF is not searchable, running OCR...")

            base_name = os.path.basename(input_pdf_path)
            temp_searchable_pdf_path = os.path.join(
                output_dir, f"searchable_{base_name}"
            )

            if ocr_pdf(input_pdf_path, temp_searchable_pdf_path, lang=lang):
                final_pdf_to_process = temp_searchable_pdf_path
            else:
                logging.error(f"Failed to OCR '{input_pdf_path}'.")
                return None # Return None if OCR fails

        # Extract text from the processed PDF
        return extract_first_page_text(final_pdf_to_process)

    finally:
        # Clean up temporary OCR'd PDF if it was created
        if temp_searchable_pdf_path and os.path.exists(temp_searchable_pdf_path):
            try:
                os.remove(temp_searchable_pdf_path)
                logging.info(
                    f"Removed temporary searchable PDF: {temp_searchable_pdf_path}"
                )
            except OSError as e:
                logging.warning(
                    f"Could not remove temporary file {temp_searchable_pdf_path}: {e}"
                )