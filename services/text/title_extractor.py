import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TitleExtractor:
    """Handles extraction and validation of book titles."""
    
    @staticmethod
    def extract_title(text: str) -> str:
        """Extract main title from the text while avoiding chapter titles."""
        try:
            # Remove table of contents section
            text = re.sub(r'(?i)^\s*(?:table of )?contents\s*(?:\n|$).*?(?=\n\s*\n|\Z)', '', text, flags=re.DOTALL|re.MULTILINE)
            
            # Patterns for actual book titles, ordered by reliability
            title_patterns = [
                # Explicit title markers
                r'(?i)^[\s\*]*(?:Title|Book Title):\s*([^\n\.]+)(?:\n|$)',
                # Standalone capitalized text at start
                r'^\s*([A-Z][^a-z\n]{2,}(?:[A-Z\s\d&,\'-]){3,})(?:\n|$)',
                # First line if properly formatted
                r'^\s*([^\n]{5,100})(?:\n|$)'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, text.strip(), re.MULTILINE)
                if match:
                    title = match.group(1).strip()
                    if TitleExtractor._is_valid_title(title):
                        return title
            
            return "Untitled Story"
        except Exception as e:
            logger.error(f"Title extraction failed: {str(e)}")
            return "Untitled Story"
    
    @staticmethod
    def _is_valid_title(title: str) -> bool:
        """Validate if extracted text is likely a proper title."""
        # Remove common invalid patterns
        if re.search(r'(?i)(chapter|section|part|volume|book)\s+\d+', title):
            return False
            
        # Check length and word count
        if len(title) < 3 or len(title) > 100:
            return False
            
        words = title.split()
        if len(words) < 1 or len(words) > 15:
            return False
            
        # Check for proper capitalization
        if not any(c.isupper() for c in title):
            return False
            
        return True
