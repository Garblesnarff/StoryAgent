"""
Core Image Generation Module
-------------------------
This module handles the core image generation functionality using Together AI's API.
It manages the API client and handles the direct interaction with the service.
"""

from together import Together
import os
import logging

logger = logging.getLogger(__name__)

class ImageGeneratorCore:
    """Handles core image generation using Together AI's API."""
    
    def __init__(self):
        """Initialize the Together AI client."""
        self.client = Together(api_key=os.environ.get('TOGETHER_AI_API_KEY'))
        
    def generate(self, prompt):
        """
        Generate an image using Together AI's API.
        
        Args:
            prompt (str): The image generation prompt
            
        Returns:
            dict: Generation result containing image URL and metadata
        """
        try:
            # Generate image using Together AI with 16:9 aspect ratio
            response = self.client.images.generate(
                prompt=prompt,
                model="black-forest-labs/FLUX.1-schnell-Free",
                width=1024,  # 16:9 ratio
                height=576,
                steps=4,
                n=1,
                response_format="b64_json"
            )
            
            if response and hasattr(response, 'data') and response.data:
                image_b64 = response.data[0].b64_json
                return {
                    'url': f"data:image/png;base64,{image_b64}",
                    'prompt': prompt
                }
                
            raise Exception("Invalid response format from image generation API")
            
        except Exception as e:
            logger.error(f"Error in image generation: {str(e)}")
            raise
