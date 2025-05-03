import argparse
import os
import sys
from parsers.pdf_parser import parse_pdf
from parsers.url_parser import parse_url
from parsers.video_parser import parse_video
from parsers.audio_parser import parse_audio


def detect_type(input_path: str) -> str:
    """Detect the type of input: pdf, url, video, audio."""
    if input_path.lower().endswith('.pdf'):
        return 'pdf'
    if input_path.lower().startswith('http'):
        return 'url'
    if any(input_path.lower().endswith(ext) for ext in ['.mp4', '.mov', '.avi', '.mkv']):
        return 'video'
    if any(input_path.lower().endswith(ext) for ext in ['.mp3', '.wav', '.flac', '.aac']):
        return 'audio'
    return 'unknown'


def main():
    parser = argparse.ArgumentParser(description='Citation extraction CLI')
    parser.add_argument('input', nargs='+', help='Input file(s) or URL(s)')
    parser.add_argument('--page-number', type=int, default=50,
                        help='Page number threshold to differentiate between books/thesis and articles (default: 50)')
    args = parser.parse_args()

    for input_path in args.input:
        ctype = detect_type(input_path)
        print(f'Processing {input_path} as {ctype}...')
        if ctype == 'pdf':
            result = parse_pdf(input_path, page_threshold=args.page_number)
        elif ctype == 'url':
            result = parse_url(input_path)
        elif ctype == 'video':
            result = parse_video(input_path)
        elif ctype == 'audio':
            result = parse_audio(input_path)
        else:
            print(f'Unknown file type for {input_path}. Skipping.')
            continue
        print('Citation:')
        print(result)
        print('-' * 40)

if __name__ == '__main__':
    main()
