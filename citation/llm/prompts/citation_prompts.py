from typing import Dict

class CitationPrompts:
    @staticmethod
    def get_metadata_extraction_prompt(text: str, doc_type: str) -> str:
        """Generate prompt for metadata extraction."""
        base_prompt = f"""Extract citation metadata from the following {doc_type} content.
Format the response as a dictionary with these fields where available:
- title
- author (Last name, First name format)
- publisher
- location
- year
- pages (format as 'pp. X-Y')
{CitationPrompts._get_type_specific_fields(doc_type)}

Content:
{text}
"""
        return base_prompt

    @staticmethod
    def get_citation_format_prompt(metadata: Dict, style: str = "chicago") -> str:
        """Generate prompt for formatting citation."""
        return f"""Format the following metadata as a {style} citation:
{metadata}

Follow these style rules:
- For books: Author Last, First. Year. Book Title. Location: Publisher.
- For articles: Author Last, First. Year. "Article Title." Journal Name (issue): pages.
- For online content: Add "Accessed Month Day, Year" at the end
- For video/audio: Add duration in (HH:MM:SS) format
"""

    @staticmethod
    def _get_type_specific_fields(doc_type: str) -> str:
        """Get additional fields based on document type."""
        type_fields = {
            'pdf': """Additional fields for PDF:
- journal (if applicable)
- conference (if applicable)
- edition (if applicable)
- volume (if applicable)
- doi (if available)""",
            
            'url': """Additional fields for URL:
- date_accessed (YYYY-MM-DD format)
- is_lecture (true/false)
- translator (if applicable)
- editor (if applicable)""",
            
            'video': """Additional fields for video:
- lecturer (if applicable)
- timeperiod (duration)
- timestamp (start-end if specified)
- date (YYYY-MM-DD format)
- url (if available)""",
            
            'audio': """Additional fields for audio:
- lecturer (if applicable)
- timeperiod (duration)
- timestamp (start-end if specified)
- date (YYYY-MM-DD format)
- url (if available)"""
        }
        return type_fields.get(doc_type, "")