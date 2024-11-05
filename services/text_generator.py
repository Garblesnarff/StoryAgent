import groq
import os
import json
import re
from .concept_generator import ConceptGenerator
from .world_builder import WorldBuilder
from .plot_weaver import PlotWeaver
import logging

logger = logging.getLogger(__name__)

class TextGenerator:
    def __init__(self):
        # Initialize Groq client and services
        self.client = groq.Groq(api_key=os.environ.get('GROQ_API_KEY'))
        self.concept_generator = ConceptGenerator()
        self.world_builder = WorldBuilder()
        self.plot_weaver = PlotWeaver()
    
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
        try:
            # Generate a detailed concept
            concept = self.concept_generator.generate_concept(prompt, genre, mood, target_audience)
            if not concept:
                logger.warning("Using fallback concept")
                concept = {
                    'core_theme': 'Growth and Change',
                    'characters': [{'name': 'Protagonist', 'description': 'A character facing challenges'}],
                    'setting': 'A world of possibilities',
                    'plot_points': ['Beginning', 'Middle', 'End'],
                    'emotional_journey': 'From struggle to triumph'
                }

            # Generate world details
            world = self.world_builder.build_world(concept, genre, mood)
            if not world:
                logger.warning("Using fallback world details")
                world = {
                    'setting': 'A mysterious realm where ancient magic and modern technology coexist.',
                    'atmosphere': 'An air of mystery and wonder pervades this timeless place.',
                    'locations': [
                        {'name': 'Central Hub', 'description': 'Where the story begins'},
                        {'name': 'Challenge Zone', 'description': 'Where conflicts unfold'}
                    ]
                }

            # Generate plot structure
            plot = self.plot_weaver.weave_plot(concept, world, genre, mood)
            if not plot:
                logger.warning("Using fallback plot structure")
                plot = {
                    'plot_outline': ['Beginning', 'Middle', 'End'],
                    'key_events': ['Introduction', 'Rising Action', 'Climax', 'Resolution'],
                    'character_arcs': [{'name': 'Protagonist', 'development': 'Growth'}],
                    'pacing_notes': 'Standard three-act structure'
                }

            # Develop detailed scenes
            scenes = self.plot_weaver.develop_scenes(plot, world)
            if not scenes:
                logger.warning("Using fallback scenes")
                scenes = {
                    'scenes': [
                        {'title': 'Opening', 'action': 'The story begins...'},
                        {'title': 'Conflict', 'action': 'Tension rises...'},
                        {'title': 'Resolution', 'action': 'The story concludes...'}
                    ],
                    'transitions': ['Beginning', 'Middle', 'End'],
                    'emotional_beats': ['Hope', 'Fear', 'Struggle', 'Resolution']
                }

            # Refine the complete plot
            refined_plot = self.plot_weaver.refine_plot(plot, scenes)
            if not refined_plot:
                logger.warning("Using fallback refined plot")
                refined_plot = {
                    'refined_plot': ['Setup', 'Conflict', 'Resolution'],
                    'story_beats': ['Introduction', 'Rising Action', 'Climax', 'Resolution'],
                    'narrative_flow': 'Classic three-act structure'
                }

            # Create an enhanced prompt using all generated elements
            enhanced_prompt = (
                f"Using this detailed story structure:\n"
                f"Theme: {concept['core_theme']}\n"
                f"Setting: {world['setting']}\n"
                f"Atmosphere: {world['atmosphere']}\n"
                f"Plot Outline: {json.dumps(plot['plot_outline'])}\n"
                f"Story Beats: {json.dumps(refined_plot['story_beats'])}\n"
                f"Narrative Flow: {refined_plot['narrative_flow']}\n\n"
                f"Write a {genre} story with a {mood} mood for a {target_audience} "
                f"audience. Create {paragraphs} distinct paragraphs that naturally "
                "flow from one to the next. Each paragraph should be 2-3 sentences. "
                "Follow the narrative flow and story beats while maintaining the core theme "
                "and incorporating vivid world details. Do not include any segment markers, "
                "numbers, or labels."
            )

            # Generate story text with the enhanced prompt
            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            f"You are a creative storyteller specializing in {genre} stories "
                            f"with a {mood} mood for a {target_audience} audience. Write in a "
                            "natural, flowing narrative style. Follow the provided structure "
                            "strictly while maintaining engaging prose."
                        )
                    },
                    {
                        "role": "user", 
                        "content": enhanced_prompt
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
                    
            return story_paragraphs[:paragraphs]
            
        except Exception as e:
            logger.error(f"Error generating story: {str(e)}")
            return None
