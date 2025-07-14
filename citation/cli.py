import argparse
import sys
import os
import logging
from citation.main import CitationExtractor
from citation.llm import get_provider_info


def main():
    parser = argparse.ArgumentParser(
        description="Extract citations from PDF files and URLs in Chicago Author-Date style."
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
        default="eng+chi_sim",
        help="Language for OCR (default: eng+chi_sim)",
    )

    # LLM model option
    provider_info = get_provider_info()
    providers_help = "; ".join([f"{k}: {v}" for k, v in provider_info.items()])
    parser.add_argument(
        "--llm",
        default="ollama/qwen3",
        help=f"LLM model to use for citation extraction (default: ollama/qwen3). "
        f"Supported providers: {providers_help}. "
        f"Examples: ollama/qwen3, gemini/gemini-1.5-flash, gemini/gemini-2.0-flash-exp",
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    try:
        # Initialize extractor with selected LLM model
        if args.verbose:
            print(f"Using LLM model: {args.llm}")
        extractor = CitationExtractor(llm_model=args.llm)

        # Auto-detect input type and process
        print(f"Processing: {args.input}")
        citation_info = extractor.extract_citation(
            args.input, args.output_dir, doc_type_override=args.type
        )

        if citation_info:
            print("\n" + "=" * 50)
            print("CITATION EXTRACTED SUCCESSFULLY")
            print("=" * 50)

            # Display extracted citation
            for key, value in citation_info.items():
                print(f"{key.replace('_', ' ').title()}: {value}")

            print(f"\nCitation files saved to: {args.output_dir}")

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
