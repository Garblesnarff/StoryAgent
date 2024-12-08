import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TextCleaner:
    """Handles text cleaning and normalization operations."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text content."""
        try:
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)
            # Normalize line endings
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            # Remove UTF-8 BOM if present
            text = text.replace('\ufeff', '')
            # Remove consecutive blank lines
            text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
            return text.strip()
        except Exception as e:
            logger.error(f"Text cleaning failed: {str(e)}")
            raise
            
    @staticmethod
    def extract_story_content(text: str) -> str:
        """Extract story content while removing boilerplate text."""
        try:
            # Remove table of contents
            clean_text = re.sub(r'(?i)^(?:table of )?contents\s*(?:\n|$).*?(?=\n\s*\n|\Z)', '', text, flags=re.DOTALL|re.MULTILINE)
            
            # Remove chapter headers and numbers
            clean_text = re.sub(r'(?i)^\s*(?:chapter|section|part|volume)\s+[IVXLCDM\d]+\.?\s*.*$', '', clean_text, flags=re.MULTILINE)
            
            # Remove common book sections
            clean_text = re.sub(r'(?i)^\s*(introduction|preface|foreword|appendix|index|bibliography).*?(?=\n\s*\n|\Z)', '', clean_text, flags=re.DOTALL|re.MULTILINE)
            
            # Remove Project Gutenberg headers and footers
            clean_text = re.sub(r'^\s*.*?\*\*\* START OF.*?\*\*\*.*?\n', '', clean_text, flags=re.DOTALL)
            clean_text = re.sub(r'\*\*\* END OF.*$', '', clean_text, flags=re.DOTALL)
            
            # Remove consecutive blank lines
            clean_text = re.sub(r'\n\s*\n\s*\n', '\n\n', clean_text)
            
            return clean_text.strip()
        except Exception as e:
            logger.error(f"Story content extraction failed: {str(e)}")
            raise
