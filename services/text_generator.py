import groq
import os
import json
import re
from typing import List, Optional, Dict, Any

class TextGenerator:
    def __init__(self):
        # Initialize Groq client
        self.client = groq.Groq(api_key=os.environ.get('GROQ_API_KEY'))
    
    def generate(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """
        Generate text with specific parameters and formatting
        
        Args:
            prompt: The prompt to send to the model
            temperature: Controls randomness in generation
            
        Returns:
            Generated text or None if generation fails
        """
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a creative writing assistant specializing in structured story generation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
            )
            
            if not response or not response.choices:
                raise Exception("No response from story generation API")
                
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating text: {str(e)}")
            return None
    
    def generate_story(self, prompt: str, genre: str, mood: str, target_audience: str, paragraphs: int) -> Optional[List[str]]:
        """Legacy method for direct story generation"""
        try:
            # Generate story text with improved prompt
            response = self.generate(
                prompt=f"Write a {genre} story with a {mood} mood for a {target_audience} audience based on this prompt: {prompt}. Write it as {paragraphs} distinct paragraphs, where each paragraph naturally flows and contains approximately 2-3 sentences. Do not include any segment markers or labels.",
                temperature=0.7
            )
            
            if not response:
                return None
            
            # Split story into paragraphs, cleaned of any potential markers
            paragraphs_raw = response.split('\n\n')
            story_paragraphs = []
            
            for paragraph in paragraphs_raw:
                # Clean the paragraph of any numbering or markers
                cleaned = re.sub(r'^[0-9]+[\.\)]\s*', '', paragraph.strip())
                cleaned = re.sub(r'Segment\s*[0-9]+:?\s*', '', cleaned)
                
                if cleaned:
                    story_paragraphs.append(cleaned)
                    
            return story_paragraphs[:paragraphs]
            
        except Exception as e:
            print(f"Error generating story: {str(e)}")
            return None
