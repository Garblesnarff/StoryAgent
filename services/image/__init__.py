"""
Image Generation Service
----------------------
This module provides the main interface for generating images using Together AI's API.
It coordinates between different components for image generation, style management,
rate limiting, and error handling.

Example usage:
    generator = ImageGenerator()
    image = generator.generate_image("A beautiful sunset", style="realistic")
"""

from .generator import ImageGeneratorCore
from .rate_limiter import RateLimiter
from .style import StyleManager
from .error_handler import ErrorHandler
import logging

logger = logging.getLogger(__name__)

class ImageGenerator:
    """Main class for handling image generation through Together AI's API."""
    
    def __init__(self):
        """Initialize the image generator with its component services."""
        self.generator = ImageGeneratorCore()
        self.rate_limiter = RateLimiter()
        self.style_manager = StyleManager()
        self.error_handler = ErrorHandler()
        
    def generate_image(self, text, style='realistic', max_retries=3, initial_delay=1):
        """
        Generate an image from the given text using Together AI's API.
        
        Args:
            text (str): Text to convert to image
            style (str): Style modifier ('realistic', 'artistic', 'fantasy')
            max_retries (int): Maximum number of retry attempts
            initial_delay (int): Initial delay between retries in seconds
            
        Returns:
            dict: Contains image URL, prompt, and generation metadata
        """
        try:
            # Apply style modifier
            enhanced_prompt = self.style_manager.apply_style(text, style)
            
            # Check rate limits
            self.rate_limiter.check_and_wait()
            
            # Generate image with error handling
            result = self.error_handler.handle_with_retries(
                lambda: self.generator.generate(enhanced_prompt),
                max_retries=max_retries,
                initial_delay=initial_delay
            )
            
            # Record rate limit
            if result and 'url' in result:
                self.rate_limiter.record_generation()
                
            return result
            
        except Exception as e:
            logger.error(f"Error in generate_image: {str(e)}")
            return {
                'error': str(e),
                'status': 'failed'
            }
            
    def generate_image_chain(self, prompts, style='realistic'):
        """
        Generate image through multiple refinement steps.
        
        Args:
            prompts (list[str]): List of prompts for refinement steps
            style (str): Style modifier to apply
            
        Returns:
            dict: Final generation result with metadata
        """
        try:
            final_result = None
            
            for i, prompt in enumerate(prompts):
                result = self.generate_image(prompt, style)
                
                if isinstance(result, dict) and 'url' in result:
                    final_result = {
                        'url': str(result['url']),
                        'prompt': str(result.get('prompt', prompt)),
                        'steps_completed': str(i + 1)
                    }
                    
                    if i < len(prompts) - 1:
                        self.rate_limiter.wait_between_steps()
                        
            return final_result
            
        except Exception as e:
            logger.error(f"Error in generate_image_chain: {str(e)}")
            return None
