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
    def _record_metrics(self, prompt_type, generation_time, success, prompt_length=0, error_msg=None):
        """Record prompt generation metrics"""
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
        # Initialize Groq client
        self.client = groq.Groq(api_key=os.environ.get('GROQ_API_KEY'))
    
    def clean_paragraph(self, text):
        """Clean paragraph text of any markers, numbers, or labels"""
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
    
    def validate_cleaned_text(self, text):
        """Check if text still contains any unwanted markers"""
        # Pattern to detect common segment markers
        marker_pattern = r'(?i)(segment|section|part|chapter|scene|\[\d+\]|\(\d+\)|^\d+\.)'
        return not bool(re.search(marker_pattern, text))

    def generate_story(self, prompt, genre, mood, target_audience, paragraphs):
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
