import groq
import os
import json
import re
from .concept_generator import ConceptGenerator
from .world_builder import WorldBuilder
from .plot_weaver import PlotWeaver

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
                raise Exception("Failed to generate story concept")

            # Generate world details
            world = self.world_builder.build_world(concept, genre, mood)
            if not world:
                raise Exception("Failed to generate world details")

            # Enhance world with genre-specific elements
            enhanced_world = self.world_builder.enhance_setting(world, genre)
            if not enhanced_world:
                raise Exception("Failed to enhance world details")

            # Generate plot structure using Plot Weaver
            plot = self.plot_weaver.weave_plot(concept, enhanced_world, genre, mood)
            if not plot:
                raise Exception("Failed to generate plot structure")

            # Develop detailed scenes
            scenes = self.plot_weaver.develop_scenes(plot, enhanced_world)
            if not scenes:
                raise Exception("Failed to develop scenes")

            # Generate dialogue if characters exist in concept
            dialogue = None
            if 'characters' in concept and concept['characters']:
                dialogue = self.plot_weaver.generate_dialogue(scenes, concept['characters'])

            # Refine the complete plot
            refined_plot = self.plot_weaver.refine_plot(plot, scenes, dialogue or {})
            if not refined_plot:
                raise Exception("Failed to refine plot")

            # Create an enhanced prompt using all generated elements
            enhanced_prompt = (
                f"Using this detailed story structure:\n"
                f"Theme: {concept['core_theme']}\n"
                f"Setting: {enhanced_world['setting']}\n"
                f"Atmosphere: {enhanced_world['atmosphere']}\n"
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
            print(f"Error generating story: {str(e)}")
            return None
