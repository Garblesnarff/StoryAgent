import groq
import os
import json
import re
import logging
import time
from database import db
from models import PromptMetric

logger = logging.getLogger(__name__)

class TextGenerator:
    """
    A service class for generating story text using the Groq LLM API.
    
    This class handles story generation tasks including text cleaning,
    validation, and performance metrics recording. It uses the Groq API
    for text generation with configurable parameters.
    """
    
    def _record_metrics(self, prompt_type: str, generation_time: float, success: bool, 
                       prompt_length: int = 0, error_msg: str = None) -> None:
        """
        Record metrics for prompt generation attempts.
        
        Args:
            prompt_type: Type of the prompt (e.g., 'story', 'chapter')
            generation_time: Time taken for generation in seconds
            success: Whether the generation was successful
            prompt_length: Length of the input prompt in characters
            error_msg: Error message if generation failed
        """
        try:
            metric = PromptMetric(
                prompt_type=prompt_type,
                generation_time=generation_time,
                num_refinement_steps=1,  # Text generation is single-step
                success=success,
                prompt_length=prompt_length,
                error_message=error_msg
            )
            db.session.add(metric)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error recording metrics: {str(e)}")
            
    def __init__(self):
        """
        Initialize the TextGenerator with Groq API client.
        Raises ValueError if GROQ_API_KEY environment variable is not set.
        """
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        self.client = groq.Groq(api_key=api_key)
    
    def clean_paragraph(self, text: str) -> str:
        """
        Clean paragraph text by removing markers, numbers, and labels.
        
        Performs the following cleaning operations:
        1. Removes leading numbers with dots, parentheses, or brackets
        2. Removes segment/section markers with optional numbers
        3. Removes standalone numbers at start
        4. Removes bracketed/parenthesized numbers
        5. Removes remaining segment markers
        6. Normalizes whitespace
        
        Args:
            text: The input text to clean
            
        Returns:
            str: The cleaned text with all markers removed
        """
        # Remove any leading numbers with dots, parentheses, or brackets
        text = re.sub(r'^\s*(?:\d+[.)\]]\s*|\[\d+\]\s*)', '', text.strip())
        
        # Remove any segment/section markers with optional numbers or colons
        text = re.sub(r'(?i)(?:segment|section|part|chapter|scene)\s*#?\d*:?\s*', '', text)
        
        # Remove any standalone numbers at start of paragraphs
        text = re.sub(r'^\s*\d+\s*', '', text)
        
        # Remove any bracketed or parenthesized numbers
        text = re.sub(r'\s*[\[\(]\d+[\]\)]\s*', ' ', text)
        
        # Remove any remaining segment-like markers
        text = re.sub(r'(?i)(?:segment|section|part|chapter|scene)\s*', '', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def validate_cleaned_text(self, text: str) -> bool:
        """
        Validate that cleaned text contains no unwanted markers.
        
        Args:
            text: The text to validate
            
        Returns:
            bool: True if text is clean, False if it contains unwanted markers
        """
        # Pattern to detect common segment markers
        marker_pattern = r'(?i)(segment|section|part|chapter|scene|\[\d+\]|\(\d+\)|^\d+\.)'
        return not bool(re.search(marker_pattern, text))

    def generate_story(self, prompt: str, genre: str, mood: str, 
                      target_audience: str, paragraphs: int) -> list[str]:
        """
        Generate a story based on given parameters using the Groq LLM.
        
        This method generates a story with the specified characteristics and
        cleans the output to ensure consistent formatting. It also records
        metrics about the generation process.
        
        Args:
            prompt: The main story prompt/idea
            genre: The story genre (e.g., 'sci-fi', 'fantasy')
            mood: The emotional tone of the story
            target_audience: The intended audience
            paragraphs: Number of paragraphs to generate
            
        Returns:
            list[str]: List of generated story paragraphs
            
        Raises:
            Exception: If story generation fails or API returns invalid response
        """
        start_time = time.time()
        success = False
        error_msg = None
        prompt_length = len(prompt) + len(genre) + len(mood) + len(target_audience)
        
        try:
            # Format the story prompt directly
            formatted_prompt = f"""
            Write a {genre} story with a {mood} mood targeting {target_audience}.
            The story should be based on the following prompt:
            {prompt}
            
            Please write {paragraphs} well-structured paragraphs.
            Each paragraph should advance the story while maintaining consistent tone and pacing.
            Focus on creating vivid imagery and engaging narrative flow.
            """
            
            # Generate story text with improved prompt
            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            f"You are a creative storyteller specializing in {genre} stories "
                            f"with a {mood} mood for a {target_audience} audience."
                        )
                    },
                    {
                        "role": "user", 
                        "content": formatted_prompt
                    }
                ],
                temperature=0.7,
            )
            
            if not response or not response.choices:
                raise Exception("No response from story generation API")
                
            story = response.choices[0].message.content
            if not story:
                raise Exception("Empty response from story generation API")
            
            # Split into paragraphs and clean each one
            paragraphs_raw = [p for p in story.split('\n\n') if p.strip()]
            story_paragraphs = []
            
            for paragraph in paragraphs_raw:
                # Clean the paragraph
                cleaned = self.clean_paragraph(paragraph)
                
                # Validate the cleaned text
                if cleaned and self.validate_cleaned_text(cleaned):
                    story_paragraphs.append(cleaned)
                else:
                    # If validation fails, try cleaning again with more aggressive patterns
                    cleaned = re.sub(r'[^a-zA-Z0-9.,!?\'"\s]', '', cleaned)
                    if cleaned:
                        story_paragraphs.append(cleaned)
                    
            success = True
            return story_paragraphs[:paragraphs]
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating story: {error_msg}")
            return None
            
        finally:
            generation_time = time.time() - start_time
            self._record_metrics(
                prompt_type='story',
                generation_time=generation_time,
                success=success,
                prompt_length=prompt_length,
                error_msg=error_msg
            )
