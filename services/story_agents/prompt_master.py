from typing import Dict, Any, List, Optional
from .base import StoryAgent
from . import StoryIdea

class PromptMaster(StoryAgent):
    """
    Agent responsible for generating initial story concepts and ideas
    """
    
    def _parse_response(self, response: str) -> Optional[StoryIdea]:
        """Parse the generated response into a StoryIdea object"""
        try:
            # Split response into sections
            sections = response.split('\n\n')
            
            # Extract title from first line
            title = sections[0].strip()
            
            # Extract concept from second section
            concept = sections[1].strip()
            
            # Extract themes from third section
            themes_text = sections[2].replace('Themes:', '').strip()
            themes = [theme.strip() for theme in themes_text.split(',')]
            
            # Extract target audience
            target_audience = sections[3].replace('Target Audience:', '').strip()
            
            # Extract estimated length
            estimated_length = sections[4].replace('Estimated Length:', '').strip()
            
            return StoryIdea(
                title=title,
                concept=concept,
                themes=themes,
                target_audience=target_audience,
                estimated_length=estimated_length
            )
        except Exception as e:
            print(f"Error parsing story idea: {str(e)}")
            return None
    
    def generate(self, context: Dict[str, Any]) -> Optional[StoryIdea]:
        """
        Generate a story idea based on the given parameters
        
        Args:
            context: Dictionary containing:
                - genre: The story genre
                - theme: Optional theme to incorporate
                - mood: The emotional tone
                - target_audience: Intended audience
                
        Returns:
            StoryIdea object or None if generation fails
        """
        prompt = f"""
        Create a compelling story idea for a {context['genre']} story with a {context.get('mood', 'neutral')} mood, 
        aimed at a {context['target_audience']} audience.
        
        {f"Incorporate the theme: {context['theme']}" if context.get('theme') else ''}
        
        Format your response as follows:
        
        [Title]
        
        [Story Concept - 2-3 sentences describing the core idea]
        
        Themes: [List main themes, separated by commas]
        
        Target Audience: [Specific target audience description]
        
        Estimated Length: [Approximate story length in paragraphs]
        """
        
        response = self._generate_with_retry(
            prompt=prompt,
            temperature=0.8  # Slightly higher temperature for more creative ideas
        )
        
        if response:
            return self._parse_response(response)
        return None
