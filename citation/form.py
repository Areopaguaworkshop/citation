from dataclasses import dataclass
from typing import Optional
from datetime import date
from enum import Enum

@dataclass
class CitationsForBook:
    author: str       # Last name and first name (e.g., "Doe, John")
    year: int
    title: str
    location: str
    publisher: str
    doi: Optional[str] = None  # Optional DOI

@dataclass
class CitationsForArticle:
    author: str       # Last name and first name (e.g., "Doe, John")
    year: int
    title: str
    container_title: str    # journal name or book name
    location: str
    publisher: str
    page_start: int
    page_end: int
    journal_number: Optional[int] = None
    volume: Optional[int] = None  # For multi-volume books
    doi: Optional[str] = None

@dataclass
class CitationsForUrl:
    author: str       # Last name and first name (e.g., "Doe, John")
    date: date       # Changed from 'data: int' to 'date: date'
    title: str      # Title of the webpage
    publisher: str
    url: str

@dataclass
class CitationsForLecture:
    author: str       # Last name and first name (e.g., "Doe, John")
    date: date       # Lecture date
    title: str       # Title of the lecture/video
    location: str    # University name or media company
    publisher: str   # Platform or institution
    video_length: Optional[str] = None  # Format: "HH:MM:SS"
    url: Optional[str] = None

class ThesisType(Enum):
    PHD = "PhD thesis"
    MASTER = "Master thesis"

@dataclass
class CitationsForThesis:
    author: str       # Last name and first name (e.g., "Doe, John")
    year: int
    title: str
    location: str
    publisher: str    # Usually university name
    thesis_type: ThesisType
    doi: Optional[str] = None
