from typing import Dict, Any, List, Optional
from .base import StoryAgent
from . import PlotHook, StoryIdea, WorldSetting

class PlotSeeder(StoryAgent):
    """
    Agent responsible for developing plot hooks and story structure
    """
    
    def _parse_response(self, response: str) -> Optional[PlotHook]:
        """Parse the generated response into a PlotHook object"""
        try:
            # Split response into sections
            sections = response.split('\n\n')
            
            # Extract inciting incident
            inciting_incident = sections[0].replace('Inciting Incident:', '').strip()
            
            # Extract stakes
            stakes = sections[1].replace('Stakes:', '').strip()
            
            # Extract potential obstacles
            obstacles_text = sections[2].replace('Potential Obstacles:', '').strip()
            obstacles = [obs.strip() for obs in obstacles_text.split(',')]
            
            # Extract character roles
            roles_text = sections[3].replace('Character Roles:', '').strip()
            roles = [role.strip() for role in roles_text.split(',')]
            
            return PlotHook(
                inciting_incident=inciting_incident,
                stakes=stakes,
                potential_obstacles=obstacles,
                character_roles=roles
            )
        except Exception as e:
            print(f"Error parsing plot hook: {str(e)}")
            return None
    
    def generate(self, context: Dict[str, Any]) -> Optional[PlotHook]:
        """
        Generate plot hooks based on the story idea and world setting
        
        Args:
            context: Dictionary containing:
                - story_idea: StoryIdea object
                - world_setting: WorldSetting object
                
        Returns:
            PlotHook object or None if generation fails
        """
        story_idea: StoryIdea = context['story_idea']
        world_setting: WorldSetting = context['world_setting']
        
        prompt = f"""
        Create compelling plot hooks for the following story:
        
        Title: {story_idea.title}
        Concept: {story_idea.concept}
        
        World Setting:
        Location: {world_setting.location}
        Time Period: {world_setting.time_period}
        Conflicts: {', '.join(world_setting.conflicts)}
        
        Format your response as follows:
        
        Inciting Incident: [Describe the event that sets the story in motion]
        
        Stakes: [Explain what's at risk and why it matters]
        
        Potential Obstacles: [List major challenges and complications, separated by commas]
        
        Character Roles: [List key character archetypes needed for the story, separated by commas]
        """
        
        response = self._generate_with_retry(
            prompt=prompt,
            temperature=0.75  # Balanced temperature for creative yet coherent plot development
        )
        
        if response:
            return self._parse_response(response)
        return None
