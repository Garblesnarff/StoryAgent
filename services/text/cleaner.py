"""
Text Cleaner Module
-----------------
This module handles text cleaning and validation for story paragraphs.
It removes unwanted markers, numbers, and ensures proper formatting.
"""

import re
import logging

logger = logging.getLogger(__name__)

class TextCleaner:
    """Handles text cleaning and validation for story paragraphs."""
    
    def clean_paragraph(self, text):
        """
        Clean paragraph text of any markers, numbers, or labels.
        
        Args:
            text (str): Raw paragraph text
            
        Returns:
            str: Cleaned paragraph text
        """
        # Remove leading numbers with dots, parentheses, or brackets
        text = re.sub(r'^\s*(?:\d+[.)\]]\s*|\[\d+\]\s*)', '', text.strip())
        
        # Remove segment/section markers with optional numbers or colons
        text = re.sub(r'(?i)(?:segment|section|part|chapter|scene)\s*#?\d*:?\s*', '', text)
        
        # Remove standalone numbers at start of paragraphs
        text = re.sub(r'^\s*\d+\s*', '', text)
        
        # Remove bracketed or parenthesized numbers
        text = re.sub(r'\s*[\[\(]\d+[\]\)]\s*', ' ', text)
        
        # Remove remaining segment-like markers
        text = re.sub(r'(?i)(?:segment|section|part|chapter|scene)\s*', '', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def validate_cleaned_text(self, text):
        """
        Check if text still contains any unwanted markers.
        
        Args:
            text (str): Cleaned text to validate
            
        Returns:
            bool: True if text is properly cleaned, False otherwise
        """
        # Pattern to detect common segment markers
        marker_pattern = r'(?i)(segment|section|part|chapter|scene|\[\d+\]|\(\d+\)|^\d+\.)'
        return not bool(re.search(marker_pattern, text))
