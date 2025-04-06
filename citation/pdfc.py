import subprocess
import os
import argparse
from grobid_client.grobid_client import GrobidClient

def run_ocr(input_pdf, output_pdf):
    """
    Use ocrmypdf to convert a scanned PDF (images only) into a searchable PDF.
    """
    try:
        # The '--skip-text' flag can be omitted if you want to force OCR even if some text is detected.
        subprocess.run(["ocrmypdf", "--skip-text", input_pdf, output_pdf], check=True)
        print(f"OCR completed: {output_pdf}")
    except subprocess.CalledProcessError as e:
        print("Error during OCR:", e)
        raise

def process_with_grobid(pdf_file, output_dir):
    """
    Use Grobid to extract bibliographic references from the searchable PDF.
    The Grobid client will send a request to the Grobid server.
    """
    # Make sure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    client = GrobidClient(config_path="config.json")
    # 'processReferences' extracts the reference section
    result = client.process("processReferences", input=pdf_file, output=output_dir)
    print("Grobid processing complete. Output files are in:", output_dir)
    return result

def main():
    parser = argparse.ArgumentParser(
        description='Process PDF files: Convert scanned PDFs to searchable PDFs and extract citations'
    )
    parser.add_argument(
        'input_pdf',
        help='Path to the input PDF file'
    )
    parser.add_argument(
        '--output-pdf',
        help='Path for the OCR-processed PDF (default: searchable_<input_name>.pdf)',
        default=None
    )
    parser.add_argument(
        '--output-dir',
        help='Directory for Grobid output (default: grobid_output)',
        default='grobid_output'
    )

    args = parser.parse_args()

    # Generate default output PDF name if not provided
    if args.output_pdf is None:
        input_name = os.path.splitext(os.path.basename(args.input_pdf))[0]
        args.output_pdf = f"searchable_{input_name}.pdf"

    # Step 1: Convert scanned PDF to searchable PDF using OCR
    run_ocr(args.input_pdf, args.output_pdf)

    # Step 2: Process the searchable PDF with Grobid to extract references
    process_with_grobid(args.output_pdf, args.output_dir)

if __name__ == "__main__":
    main()