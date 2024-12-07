"""
Audio Generation Utilities
------------------------
Provides utility functions and classes for audio generation,
including retry logic and error handling.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class RetryManager:
    """Manages retry logic for failed operations."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """
        Initialize the retry manager.
        
        Args:
            max_retries (int): Maximum number of retry attempts
            base_delay (float): Base delay for exponential backoff in seconds
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        
    async def handle_retry(self, retry_count: int) -> None:
        """
        Handle retry logic with exponential backoff.
        
        Args:
            retry_count (int): Current retry attempt number
        """
        if retry_count >= self.max_retries:
            return
            
        delay = self.base_delay * (2 ** (retry_count - 1))  # Exponential backoff
        logger.info(f"Retrying after {delay} seconds (attempt {retry_count}/{self.max_retries})")
        await asyncio.sleep(delay)
        
    def should_retry(self, retry_count: int) -> bool:
        """
        Determine if another retry attempt should be made.
        
        Args:
            retry_count (int): Current retry attempt number
            
        Returns:
            bool: True if should retry, False otherwise
        """
        return retry_count < self.max_retries
        
class ChunkManager:
    """Manages text chunking and processing strategies."""
    
    @staticmethod
    def is_complete_sentence(text: str) -> bool:
        """
        Check if text ends with a sentence-ending punctuation.
        
        Args:
            text (str): Text to check
            
        Returns:
            bool: True if text ends with sentence punctuation
        """
        return text.strip().endswith(('.', '!', '?'))
        
    @staticmethod
    def ensure_complete_sentence(text: str) -> str:
        """
        Ensure text ends with proper sentence punctuation.
        
        Args:
            text (str): Text to process
            
        Returns:
            str: Text with proper sentence ending
        """
        text = text.strip()
        if not ChunkManager.is_complete_sentence(text):
            text += '.'
        return text
