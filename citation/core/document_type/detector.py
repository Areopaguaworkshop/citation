from typing import Literal, Dict, Any

DocumentType = Literal['pdf', 'url', 'video', 'audio']
CitationType = Literal['book', 'article', 'conference_paper', 'thesis', 'online_lecture', 'online_article', 'video', 'audio']

class DocumentDetector:
    def __init__(self, page_threshold: int = 50):
        self.page_threshold = page_threshold

    def detect_type(self, file_path: str) -> DocumentType:
        """Detect the type of input: pdf, url, video, audio."""
        lower_path = file_path.lower()
        if lower_path.endswith('.pdf'):
            return 'pdf'
        if lower_path.startswith('http'):
            return 'url'
        if any(lower_path.endswith(ext) for ext in ['.mp4', '.mov', '.avi', '.mkv']):
            return 'video'
        if any(lower_path.endswith(ext) for ext in ['.mp3', '.wav', '.flac', '.aac']):
            return 'audio'
        raise ValueError(f"Unsupported file type: {file_path}")

    def detect_citation_type(self, metadata: Dict[str, Any]) -> CitationType:
        """Determine the citation type based on document metadata."""
        doc_type = metadata.get('type', '')
        page_count = metadata.get('page_count', 0)
        
        if doc_type == 'pdf':
            if 'thesis' in metadata.get('file_path', '').lower():
                return 'thesis'
            elif page_count >= self.page_threshold:
                return 'book'
            else:
                if metadata.get('journal'):
                    return 'article'
                elif metadata.get('conference'):
                    return 'conference_paper'
                return 'article'  # Default for short PDFs
        elif doc_type == 'url':
            if metadata.get('is_lecture', False):
                return 'online_lecture'
            return 'online_article'
        elif doc_type == 'video':
            return 'video'
        elif doc_type == 'audio':
            return 'audio'
        
        raise ValueError(f"Unable to determine citation type for metadata: {metadata}")