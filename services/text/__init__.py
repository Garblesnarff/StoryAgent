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
import os
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Import service classes
from .text_extractor import TextExtractor
from .text_cleaner import TextCleaner
from .text_chunker import TextChunker
from .title_extractor import TitleExtractor
from .validation_service import ValidationService

# Ensure required directories exist
os.makedirs('uploads', exist_ok=True)

__all__ = [
    'TextExtractor',
    'TextCleaner',
    'TextChunker',
    'TitleExtractor',
    'ValidationService'
]
