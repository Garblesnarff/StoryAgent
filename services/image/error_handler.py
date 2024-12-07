"""
Error Handling Module
------------------
This module handles error recovery and retry logic for image generation.
It provides consistent error handling and retry behavior across the service.
"""

import time
import logging

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Handles error recovery and retries for image generation."""
    
    def handle_with_retries(self, operation, max_retries=3, initial_delay=1):
        """
        Execute an operation with retry logic.
        
        Args:
            operation: Callable to execute
            max_retries (int): Maximum number of retry attempts
            initial_delay (int): Initial delay between retries in seconds
            
        Returns:
            dict: Operation result or error information
        """
        retry_count = 0
        current_delay = initial_delay
        last_error = None
        
        while retry_count < max_retries:
            try:
                return operation()
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                if retry_count < max_retries:
                    logger.warning(
                        f"Attempt {retry_count} failed: {str(e)}. "
                        f"Retrying in {current_delay} seconds..."
                    )
                    time.sleep(current_delay)
                    current_delay *= 2  # Exponential backoff
                else:
                    logger.error(
                        f"All attempts failed after {max_retries} retries. "
                        f"Last error: {str(e)}"
                    )
        
        # If we get here, all retries failed
        raise last_error
