from typing import Dict, Any, Optional, Tuple
from services.text_generator import TextGenerator
from .prompt_master import PromptMaster
from .world_shaper import WorldShaper
from .plot_seeder import PlotSeeder
from . import StoryIdea, WorldSetting, PlotHook

class IdeaGenerationCrew:
    """
    Orchestrates the story generation agents to create a complete story concept
    """
    
    def __init__(self, text_generator: TextGenerator):
        self.prompt_master = PromptMaster(text_generator)
        self.world_shaper = WorldShaper(text_generator)
        self.plot_seeder = PlotSeeder(text_generator)
    
    def generate_story_concept(
        self,
        genre: str,
        theme: Optional[str] = None,
        mood: Optional[str] = None,
        target_audience: str = "general"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a complete story concept with world building and plot hooks
        
        Args:
            genre: The story genre
            theme: Optional theme to incorporate
            mood: Optional emotional tone
            target_audience: Intended audience
            
        Returns:
            Dictionary containing story_idea, world_setting, and plot_hook,
            or None if generation fails
        """
        try:
            # Generate initial story idea
            story_idea = self.prompt_master.generate({
                'genre': genre,
                'theme': theme,
                'mood': mood,
                'target_audience': target_audience
            })
            
            if not story_idea:
                return None
            
            # Generate world setting based on story idea
            world_setting = self.world_shaper.generate({
                'story_idea': story_idea,
                'genre': genre
            })
            
            if not world_setting:
                return None
            
            # Generate plot hooks based on story idea and world
            plot_hook = self.plot_seeder.generate({
                'story_idea': story_idea,
                'world_setting': world_setting
            })
            
            if not plot_hook:
                return None
            
            return {
                'story_idea': story_idea.__dict__,
                'world_setting': world_setting.__dict__,
                'plot_hook': plot_hook.__dict__
            }
            
        except Exception as e:
            print(f"Error in story concept generation: {str(e)}")
            return None
