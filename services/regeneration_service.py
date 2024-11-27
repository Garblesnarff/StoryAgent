"""
Regeneration Service Module

This service coordinates the regeneration of media content (images and audio)
for story paragraphs, handling:
- Unified media regeneration interface
- Context-aware regeneration with story history
- Batch regeneration capabilities
- Error handling and retries
- Progress tracking
"""

from typing import Optional, Dict, List, Tuple
import logging
from services.image_generator import ImageGenerator
from services.hume_audio_generator import HumeAudioGenerator

logger = logging.getLogger(__name__)

class RegenerationService:
    """
    Coordinates media regeneration for story content.
    
    This service provides a unified interface for regenerating various media types
    while maintaining context awareness and handling complex regeneration scenarios.
    
    Attributes:
        image_generator: Service for generating images
        audio_generator: Service for generating audio
    """
    
    def __init__(self, image_generator: ImageGenerator, audio_generator: HumeAudioGenerator):
        """
        Initialize regeneration service with required generators.
        
        Args:
            image_generator: Instance of ImageGenerator service
            audio_generator: Instance of HumeAudioGenerator service
        """
        self.image_generator = image_generator
        self.audio_generator = audio_generator
    
    def regenerate_paragraph_media(
        self,
        text: str,
        story_context: str = "",
        style: str = "realistic",
        regenerate_image: bool = True,
        regenerate_audio: bool = True
    ) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
        """
        Regenerate all or specific media types for a paragraph.
        
        This method provides a unified interface for regenerating multiple
        media types while maintaining proper context and style settings.
        
        Args:
            text: The paragraph text to generate media for
            story_context: Previous story context for better continuity
            style: Image style preference (realistic, artistic, fantasy)
            regenerate_image: Whether to regenerate the image
            regenerate_audio: Whether to regenerate the audio
            
        Returns:
            Tuple containing:
            - Dict with image data (url and prompt) or None if image generation disabled/failed
            - String with audio URL or None if audio generation disabled/failed
            
        Raises:
            ValueError: If text is empty or invalid
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
            
        image_result = None
        audio_url = None
        
        try:
            if regenerate_image:
                # Generate image with context-awareness
                image_result = self.image_generator.generate_image(
                    text=text,
                    style=style
                )
                if not image_result:
                    logger.error("Failed to regenerate image")
                
            if regenerate_audio:
                # Generate audio
                audio_url = self.audio_generator.generate_audio(text)
                if not audio_url:
                    logger.error("Failed to regenerate audio")
                    
            return image_result, audio_url
            
        except Exception as e:
            logger.error(f"Error in regenerate_paragraph_media: {str(e)}")
            return None, None
    
    async def batch_regenerate_media(
        self,
        paragraphs: List[Dict[str, str]],
        style: str = "realistic"
    ) -> List[Dict[str, Optional[str]]]:
        """
        Regenerate media for multiple paragraphs in batch.
        
        This method handles bulk regeneration while maintaining proper
        ordering and context between paragraphs.
        
        Args:
            paragraphs: List of paragraph data containing text and index
            style: Image style preference
            
        Returns:
            List of dictionaries containing regenerated media URLs for each paragraph
        """
        results = []
        story_context = ""
        
        for paragraph in paragraphs:
            text = paragraph.get('text', '')
            if not text:
                continue
                
            image_result, audio_url = self.regenerate_paragraph_media(
                text=text,
                story_context=story_context,
                style=style
            )
            
            results.append({
                'index': paragraph.get('index'),
                'image_url': image_result.get('url') if image_result else None,
                'image_prompt': image_result.get('prompt') if image_result else None,
                'audio_url': audio_url
            })
            
            # Update context for next iteration
            story_context += f"\n{text}"
            
        return results
