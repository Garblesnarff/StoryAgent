
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
    
    def _make_api_call(self, formatted_prompt, system_content):
        """Make an API call to the Groq chat completions endpoint.
        
        Args:
            formatted_prompt (str): The formatted prompt to send to the API
            system_content (str): The system role content for context
            
        Returns:
            dict: Contains 'story' (str) if successful, None if failed
                 and 'error' (str) with error message if failed
        """
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": system_content
                    },
                    {
                        "role": "user",
                        "content": formatted_prompt
                    }
                ],
                temperature=0.7,
            )
            
            if not response or not response.choices:
                return {"story": None, "error": "No response from story generation API"}
                
            story = response.choices[0].message.content
            if not story:
                return {"story": None, "error": "Empty response from story generation API"}
                
            return {"story": story, "error": None}

        except groq.APIError as e:
            # Log more details from Groq API errors
            error_details = f"Groq API Error: Status={e.status_code}, Response={getattr(e, 'response', 'N/A')}, Body={getattr(e, 'body', 'N/A')}"
            logger.error(error_details)
            return {"story": None, "error": f"API Error: {str(e)}"}
        except Exception as e:
            # Catch other potential errors
            logger.error(f"Unexpected error during API call: {str(e)}", exc_info=True)
            return {"story": None, "error": f"Unexpected error: {str(e)}"}

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
        """Generate a story based on given parameters.
        
        Args:
            prompt (str): The story prompt
            genre (str): The story genre
            mood (str): The desired mood
            target_audience (str): The target audience
            paragraphs (int): Number of paragraphs to generate
            
        Returns:
            list: List of cleaned story paragraphs if successful, None if failed
        """
        start_time = time.time()
        success = False
        error_msg = None
        prompt_length = len(prompt) + len(genre) + len(mood) + len(target_audience)
        
        try:
            formatted_prompt = f"""
            Write a {genre} story with a {mood} mood targeting {target_audience}.
            The story should be based on the following prompt:
            {prompt}
            
            Please write {paragraphs} well-structured paragraphs.
            Each paragraph should advance the story while maintaining consistent tone and pacing.
            Focus on creating vivid imagery and engaging narrative flow.
            """
            
            system_content = (
                f"You are a creative storyteller specializing in {genre} stories "
                f"with a {mood} mood for a {target_audience} audience."
            )
            
            result = self._make_api_call(formatted_prompt, system_content)
            
            if result["error"]:
                error_msg = result["error"]
                return None
                
            story = result["story"]
            
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
