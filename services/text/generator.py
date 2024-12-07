"""
Story Generator Module
--------------------
This module handles the core story generation functionality using LLM providers.
It formats prompts and manages the interaction with the LLM API.
"""

import groq
import os
import logging
import time

logger = logging.getLogger(__name__)

class StoryGenerator:
    """Handles core story generation using LLM providers."""
    
    def __init__(self):
        """Initialize the LLM client."""
        self.client = groq.Groq(api_key=os.environ.get('GROQ_API_KEY'))
        
    def _format_prompt(self, prompt, genre, mood, target_audience, paragraphs):
        """Format the story generation prompt."""
        return f"""
        Write a {genre} story with a {mood} mood targeting {target_audience}.
        The story should be based on the following prompt:
        {prompt}
        
        Please write {paragraphs} well-structured paragraphs.
        Each paragraph should advance the story while maintaining consistent tone and pacing.
        Focus on creating vivid imagery and engaging narrative flow.
        """
        
    def generate(self, prompt, genre, mood, target_audience, paragraphs):
        """
        Generate story text using the LLM.
        
        Args:
            prompt (str): Story prompt
            genre (str): Story genre
            mood (str): Story mood/tone
            target_audience (str): Target audience
            paragraphs (int): Number of paragraphs
            
        Returns:
            list[str]: Generated paragraphs
        """
        try:
            formatted_prompt = self._format_prompt(
                prompt, genre, mood, target_audience, paragraphs
            )
            
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
            
            return [p for p in story.split('\n\n') if p.strip()]
            
        except Exception as e:
            logger.error(f"Error in story generation: {str(e)}")
            raise
