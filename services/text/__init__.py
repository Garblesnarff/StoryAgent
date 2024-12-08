"""
Text Processing Services
----------------------
This module provides specialized services for processing book text content.
It includes services for text extraction, cleaning, chunking, title extraction,
and validation operations.

Example usage:
    extractor = TextExtractor()
    cleaner = TextCleaner()
    text = extractor.extract_from_pdf("book.pdf")
    clean_text = cleaner.clean_text(text)
"""

import logging
from datetime import datetime
from .text_extractor import TextExtractor
from .text_cleaner import TextCleaner
from .text_chunker import TextChunker
from .title_extractor import TitleExtractor
from .validation_service import ValidationService

logger = logging.getLogger(__name__)

__all__ = [
    'TextExtractor',
    'TextCleaner',
    'TextChunker',
    'TitleExtractor',
    'ValidationService'
]
