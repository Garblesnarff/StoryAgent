from typing import Dict, Any, List, Optional
from .base import StoryAgent
from . import WorldSetting, StoryIdea

class WorldShaper(StoryAgent):
    """
    Agent responsible for developing the story's world and setting
    """
    
    def _parse_response(self, response: str) -> Optional[WorldSetting]:
        """Parse the generated response into a WorldSetting object"""
        try:
            # Split response into sections
            sections = response.split('\n\n')
            
            # Extract location
            location = sections[0].replace('Location:', '').strip()
            
            # Extract time period
            time_period = sections[1].replace('Time Period:', '').strip()
            
            # Extract cultural elements
            cultural_elements_text = sections[2].replace('Cultural Elements:', '').strip()
            cultural_elements = [elem.strip() for elem in cultural_elements_text.split(',')]
            
            # Extract key locations
            key_locations_text = sections[3].replace('Key Locations:', '').strip()
            key_locations = [loc.strip() for loc in key_locations_text.split(',')]
            
            # Extract conflicts
            conflicts_text = sections[4].replace('Conflicts:', '').strip()
            conflicts = [conflict.strip() for conflict in conflicts_text.split(',')]
            
            return WorldSetting(
                location=location,
                time_period=time_period,
                cultural_elements=cultural_elements,
                key_locations=key_locations,
                conflicts=conflicts
            )
        except Exception as e:
            print(f"Error parsing world setting: {str(e)}")
            return None
    
    def generate(self, context: Dict[str, Any]) -> Optional[WorldSetting]:
        """
        Generate a world setting based on the story idea and genre
        
        Args:
            context: Dictionary containing:
                - story_idea: StoryIdea object
                - genre: The story genre
                
        Returns:
            WorldSetting object or None if generation fails
        """
        story_idea: StoryIdea = context['story_idea']
        genre = context['genre']
        
        prompt = f"""
        Create a rich and detailed world setting for the following story:
        
        Title: {story_idea.title}
        Concept: {story_idea.concept}
        Genre: {genre}
        
        Format your response as follows:
        
        Location: [Describe the primary setting/location]
        
        Time Period: [Specify the time period or era]
        
        Cultural Elements: [List key cultural elements, customs, or societal norms, separated by commas]
        
        Key Locations: [List important locations within the main setting, separated by commas]
        
        Conflicts: [List major environmental, societal, or situational conflicts present in this world, separated by commas]
        """
        
        response = self._generate_with_retry(
            prompt=prompt,
            temperature=0.7  # Balanced temperature for consistent world-building
        )
        
        if response:
            return self._parse_response(response)
        return None
