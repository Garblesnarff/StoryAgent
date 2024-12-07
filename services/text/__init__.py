"""
Text Generation Service
----------------------
This module provides the main interface for generating story text using various LLM providers.
It coordinates between different components for text generation, cleaning, and metrics recording.

Example usage:
    generator = TextGenerator()
    story = generator.generate_story("A hero's journey", "fantasy", "epic", "young adult", 5)
"""

from .generator import StoryGenerator
from .cleaner import TextCleaner
from .metrics import MetricsRecorder

class TextGenerator:
    """Main class for handling text generation through LLM providers."""
    
    def __init__(self):
        """Initialize the text generator with its component services."""
        self.generator = StoryGenerator()
        self.cleaner = TextCleaner()
        self.metrics = MetricsRecorder()
        
    def generate_story(self, prompt, genre, mood, target_audience, paragraphs):
        """
        Generate a story based on the given parameters.
        
        Args:
            prompt (str): The story prompt
            genre (str): Genre of the story
            mood (str): Mood/tone of the story
            target_audience (str): Target audience
            paragraphs (int): Number of paragraphs to generate
            
        Returns:
            list[str]: List of generated story paragraphs
        """
        start_time = time.time()
        success = False
        error_msg = None
        prompt_length = len(prompt) + len(genre) + len(mood) + len(target_audience)
        
        try:
            story_paragraphs = self.generator.generate(
                prompt, genre, mood, target_audience, paragraphs
            )
            
            # Clean and validate paragraphs
            cleaned_paragraphs = []
            for paragraph in story_paragraphs:
                cleaned = self.cleaner.clean_paragraph(paragraph)
                if self.cleaner.validate_cleaned_text(cleaned):
                    cleaned_paragraphs.append(cleaned)
                    
            success = True
            return cleaned_paragraphs[:paragraphs]
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating story: {error_msg}")
            return None
            
        finally:
            # Record metrics
            self.metrics.record(
                'story',
                time.time() - start_time,
                success,
                prompt_length,
                error_msg
            )
