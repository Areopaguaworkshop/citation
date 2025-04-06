from pathlib import Path
from typing import Union
import argparse
import sys
from model import pdf_search
from form import CitationsForBook, CitationsForThesis

def process_pdf(pdf_path: str) -> Union[CitationsForBook, CitationsForThesis]:
    """
    Process a PDF file and return citation information.
    
    Args:
        pdf_path: Path to the PDF file
    Returns:
        Citation object (either book or thesis)
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    if path.suffix.lower() != '.pdf':
        raise ValueError(f"File must be a PDF: {pdf_path}")
    
    return pdf_search(str(path))

def main():
    parser = argparse.ArgumentParser(
        description="Extract citation information from PDF documents"
    )
    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to the PDF file"
    )
    
    args = parser.parse_args()
    
    try:
        citation = process_pdf(args.pdf_path)
        print(f"\nCitation Information:")
        for field in citation.__dataclass_fields__:
            value = getattr(citation, field)
            if value is not None:
                print(f"{field}: {value}")
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
