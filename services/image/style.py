"""
Style Management Module
--------------------
This module handles style modifications for image generation prompts.
It provides consistent styling across different generation requests.
"""

import logging

logger = logging.getLogger(__name__)

class StyleManager:
    """Handles style modifications for image generation prompts."""
    
    def __init__(self):
        """Initialize style modifiers."""
        self.style_modifiers = {
            'realistic': 'A photorealistic image with natural lighting and detailed textures showing',
            'artistic': 'An artistic interpretation with expressive brushstrokes and vibrant colors depicting',
            'fantasy': 'A magical and ethereal fantasy scene with mystical elements portraying'
        }
        
    def apply_style(self, text, style='realistic'):
        """
        Apply style modifier to the prompt text.
        
        Args:
            text (str): Base prompt text
            style (str): Style to apply ('realistic', 'artistic', 'fantasy')
            
        Returns:
            str: Modified prompt with style applied
        """
        modifier = self.style_modifiers.get(style, self.style_modifiers['realistic'])
        return f"{modifier}: {text}"
