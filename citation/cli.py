import argparse
import sys
from citation.main import get_pdf_citation_text

def main():
    parser = argparse.ArgumentParser(description='Extracts citation text from the first page of a PDF.')
    parser.add_argument('input_pdf', help='Path to the input PDF file.')
    parser.add_argument('--lang', '-l', default='eng', help='Language for OCR (e.g., eng, chi_sim).')

    args = parser.parse_args()

    # This will now return the raw text from the first page.
    text = get_pdf_citation_text(args.input_pdf, lang=args.lang)

    if text:
        # The agent will process this raw text output.
        print(text)
    else:
        print("Could not extract text from the PDF.", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
