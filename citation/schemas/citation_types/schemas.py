from typing import Dict, Any
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List

class BaseCitation(BaseModel):
    """Base model for all citation types"""
    title: str
    publisher: str
    location: str
    type: str
    citation_type: str
    citation_style: str = Field(default="chicago")

class BookCitation(BaseCitation):
    """Schema for book citations"""
    author: str
    year: int
    pages: str
    edition: Optional[str] = None
    volume: Optional[str] = None
    series: Optional[str] = None
    isbn: Optional[str] = None
    doi: Optional[str] = None
    editor: Optional[str] = None
    translator: Optional[str] = None

class ArticleCitation(BaseCitation):
    """Schema for article citations"""
    author: str
    year: int
    journal: str
    pages: str
    volume: Optional[str] = None
    doi: Optional[str] = None

class ThesisCitation(BaseCitation):
    """Schema for thesis citations"""
    author: str
    year: int
    pages: str
    thesis_type: str = Field(..., regex='^(PhD|MA)$')
    university: str
    advisor: Optional[str] = None
    committee: Optional[List[str]] = None
    defense_date: Optional[date] = None

class OnlineCitation(BaseCitation):
    """Schema for online content citations"""
    date: date
    date_accessed: date
    url: str
    author: Optional[str] = None
    editor: Optional[str] = None
    translator: Optional[str] = None

class MediaCitation(BaseCitation):
    """Schema for video/audio citations"""
    lecturer: str
    date: date
    date_accessed: date
    timeperiod: str
    timestamp: Optional[str] = None
    url: Optional[str] = None

def validate_citation(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Validate citation metadata against appropriate schema"""
    citation_type = metadata.get('citation_type', '').lower()
    
    schema_map = {
        'book': BookCitation,
        'article': ArticleCitation,
        'thesis': ThesisCitation,
        'online_article': OnlineCitation,
        'online_lecture': OnlineCitation,
        'video': MediaCitation,
        'audio': MediaCitation
    }
    
    if citation_type not in schema_map:
        raise ValueError(f"Unknown citation type: {citation_type}")
        
    schema = schema_map[citation_type]
    validated = schema(**metadata)
    return validated.model_dump(exclude_none=True)