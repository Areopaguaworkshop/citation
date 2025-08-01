import argparse
import sys
import os
import logging
from citation.main import CitationExtractor
from citation.llm import get_provider_info
from citation.citation_style import format_bibliography


def main():
    parser = argparse.ArgumentParser(
        description="Extract citations from PDF files and URLs."
    )

    # Input (auto-detected)
    parser.add_argument(
        "input", help="Path to PDF file or URL to extract citation from"
    )

    # Document type option
    parser.add_argument(
        "--type",
        "-t",
        choices=["book", "thesis", "journal", "bookchapter"],
        help="Document type (overrides automatic detection based on page count)",
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        "-o",
        default="example",
        help="Output directory for citation files (default: example)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    # Language option for OCR
    parser.add_argument(
        "--lang",
        "-l",
        default="auto",
        help="Language for OCR. Default is 'auto' for automatic detection. "
             "Example: 'eng+chi_sim'.",
    )

    # Text direction option for PDFs
    parser.add_argument(
        "--text-direction",
        "-td",
        choices=["horizontal", "auto", "vertical"],
        default="horizontal",
        help="Text direction for PDF processing. 'auto' or 'vertical' is recommended for "
             "documents with vertical text, common in Chinese and Japanese. "
             "This option only applies to PDF files. Default: horizontal.",
    )

    # Language option for vertical OCR
    parser.add_argument(
        "--vertical-lang",
        choices=["ch", "japan"],
        default="ch",
        help="Primary language for vertical text OCR (default: ch)",
    )

    # Page range option for OCR
    parser.add_argument(
        "--page-range",
        "-p",
        default="1-5, -3",
        help='Page range for OCR. Examples: "1-5", "1,3,5", "-3", "1-5, -3". Default: "1-5, -3"',
    )

    # LLM model option
    provider_info = get_provider_info()
    providers_help = "; ".join([f"{k}: {v}" for k, v in provider_info.items()])
    parser.add_argument(
        "--llm",
        default="ollama/qwen3",
        help=f"LLM model to use for citation extraction (default: ollama/qwen3). "
        f"Supported providers: {providers_help}. "
        f"Examples: ollama/qwen3, gemini/gemini-1.5-flash",
    )

    # Citation style option
    parser.add_argument(
        "--citation-style",
        "-cs",
        default="chicago-author-date",
        help="Citation style for formatted output (default: chicago-author-date). "
             "Place CSL files in the 'citation/styles' directory."
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    # Check if --text-direction is used with a non-PDF file
    if args.text_direction != "horizontal" and not args.input.lower().endswith(".pdf"):
        print(
            "Warning: --text-direction is only applicable to PDF files and will be ignored.",
            file=sys.stderr,
        )

    try:
        # Initialize extractor with selected LLM model
        if args.verbose:
            print(f"Using LLM model: {args.llm}")
        extractor = CitationExtractor(llm_model=args.llm)

        # Auto-detect input type and process
        print(f"Processing: {args.input}")
        csl_data = extractor.extract_citation(
            args.input,
            output_dir=args.output_dir,
            doc_type_override=args.type,
            lang=args.lang,
            text_direction=args.text_direction,
            vertical_lang=args.vertical_lang,
            page_range=args.page_range,
        )

        if csl_data:
            print("\n" + "=" * 50)
            print("CITATION EXTRACTED SUCCESSFULLY")
            print("=" * 50)
            
            # Display raw CSL data
            for key, value in csl_data.items():
                print(f"{key.replace('_', ' ').title()}: {value}")
            print(f"\nCitation files saved to: {args.output_dir}")

            # Display formatted bibliography
            print("\n" + "=" * 50)
            print(f"FORMATTED BIBLIOGRAPHY ({args.citation_style})")
            print("=" * 50)
            
            bibliography, in_text_citation = format_bibliography([csl_data], args.citation_style)
            
            print(bibliography)
            
            print("\n" + "=" * 50)
            print("IN-TEXT CITATION")
            print("=" * 50)
            print(in_text_citation)


        else:
            print("Failed to extract citation information.", file=sys.stderr)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
