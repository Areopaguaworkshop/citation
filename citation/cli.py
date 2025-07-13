import argparse
import sys
import os
import logging
from citation.main import CitationExtractor

def main():
    parser = argparse.ArgumentParser(
        description='Extract citations from PDF files and URLs in Chicago Author-Date style.'
    )
    
    # Input type
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--pdf', '-p', help='Path to the input PDF file')
    input_group.add_argument('--url', '-u', help='URL to extract citation from')
    
    # Output options
    parser.add_argument('--output-dir', '-o', default='citations', 
                       help='Output directory for citation files (default: citations)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    # Language option for OCR
    parser.add_argument('--lang', '-l', default='eng+chi_sim', 
                       help='Language for OCR (default: eng+chi_sim)')
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    try:
        # Initialize extractor
        extractor = CitationExtractor()
        
        if args.pdf:
            # Validate PDF file exists
            if not os.path.exists(args.pdf):
                print(f"Error: PDF file not found: {args.pdf}", file=sys.stderr)
                sys.exit(1)
            
            print(f"Processing PDF: {args.pdf}")
            citation_info = extractor.extract_from_pdf(args.pdf, args.output_dir)
            
        elif args.url:
            print(f"Processing URL: {args.url}")
            citation_info = extractor.extract_from_url(args.url, args.output_dir)
        
        if citation_info:
            print("\n" + "="*50)
            print("CITATION EXTRACTED SUCCESSFULLY")
            print("="*50)
            
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

if __name__ == '__main__':
    main()
