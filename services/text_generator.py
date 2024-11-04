import groq
import os
import json
import re
from flask import current_app, Response, stream_with_context
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
    
    def emit_progress(self, agent, status, progress, task, overall_progress=None):
        """Emit progress event for streaming"""
        data = {
            'agent': agent,
            'status': status,
            'progress': progress,
            'task': task
        }
        if overall_progress is not None:
            data['overall_progress'] = overall_progress
        return f"data: {json.dumps(data)}\n\n"
    
    def clean_paragraph(self, text):
        """Clean paragraph text of any markers, numbers, or labels"""
        text = re.sub(r'^\s*(?:\d+[.)\]]\s*|\[\d+\]\s*)', '', text.strip())
        text = re.sub(r'(?i)(?:segment|section|part|chapter|scene)\s*#?\d*:?\s*', '', text)
        text = re.sub(r'^\s*\d+\s*', '', text)
        text = re.sub(r'\s*[\[\(]\d+[\]\)]\s*', ' ', text)
        text = re.sub(r'(?i)(?:segment|section|part|chapter|scene)\s*', '', text)
        text = ' '.join(text.split())
        return text.strip()
    
    def validate_cleaned_text(self, text):
        """Check if text still contains any unwanted markers"""
        marker_pattern = r'(?i)(segment|section|part|chapter|scene|\[\d+\]|\(\d+\)|^\d+\.)'
        return not bool(re.search(marker_pattern, text))

    def generate_story(self, prompt, genre, mood, target_audience, paragraphs):
        try:
            # Start with Concept Generator
            yield self.emit_progress('concept-generator', 'active', 0, 'Generating initial premise...', 0)
            
            concept = self.concept_generator.generate_concept(prompt, genre, mood, target_audience)
            if not concept:
                raise Exception("Failed to generate story concept")
            
            yield self.emit_progress('concept-generator', 'completed', 100, 'Concept generation complete!', 25)
            yield self.emit_progress('world-builder', 'active', 0, 'Building world foundation...', 25)

            # Generate world details
            world = self.world_builder.build_world(concept, genre, mood)
            if not world:
                raise Exception("Failed to generate world details")
            
            yield self.emit_progress('world-builder', 'active', 50, 'Enhancing world details...', 35)

            # Enhance world with genre-specific elements
            enhanced_world = self.world_builder.enhance_setting(world, genre)
            if not enhanced_world:
                raise Exception("Failed to enhance world details")
            
            yield self.emit_progress('world-builder', 'completed', 100, 'World building complete!', 50)
            yield self.emit_progress('plot-weaver', 'active', 0, 'Weaving initial plot structure...', 50)

            # Generate plot structure using Plot Weaver
            plot = self.plot_weaver.weave_plot(concept, enhanced_world, genre, mood)
            if not plot:
                raise Exception("Failed to generate plot structure")
            
            yield self.emit_progress('plot-weaver', 'active', 25, 'Developing detailed scenes...', 60)

            # Develop detailed scenes
            scenes = self.plot_weaver.develop_scenes(plot, enhanced_world)
            if not scenes:
                raise Exception("Failed to develop scenes")
            
            yield self.emit_progress('plot-weaver', 'active', 50, 'Generating character dialogue...', 70)

            # Generate dialogue if characters exist in concept
            dialogue = None
            if 'characters' in concept and concept['characters']:
                dialogue = self.plot_weaver.generate_dialogue(scenes, concept['characters'])
            
            yield self.emit_progress('plot-weaver', 'active', 75, 'Refining plot structure...', 80)

            # Refine the complete plot
            refined_plot = self.plot_weaver.refine_plot(plot, scenes, dialogue or {})
            if not refined_plot:
                raise Exception("Failed to refine plot")
            
            yield self.emit_progress('plot-weaver', 'completed', 100, 'Plot weaving complete!', 90)
            yield self.emit_progress('story-generator', 'active', 0, 'Generating final story...', 90)

            # Create an enhanced prompt using all generated elements
            enhanced_prompt = (
                f"Using this detailed story structure:\n"
                f"Theme: {concept['core_theme']}\n"
                f"Setting: {enhanced_world['setting']}\n"
                f"Atmosphere: {enhanced_world['atmosphere']}\n"
                f"Plot Points: {json.dumps(plot['plot_points'])}\n"
                f"Character Arcs: {json.dumps(plot['character_arcs'])}\n"
                f"Story Flow: {plot['narrative_flow']}\n\n"
                f"Write a {genre} story with a {mood} mood for a {target_audience} "
                f"audience. Create {paragraphs} distinct paragraphs that naturally "
                "flow from one to the next. Each paragraph should be 2-3 sentences. "
                "Follow the narrative flow and plot points while maintaining the core theme "
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
            
            for i, paragraph in enumerate(paragraphs_raw):
                yield self.emit_progress('story-generator', 'active', 
                                      int((i + 1) / len(paragraphs_raw) * 100),
                                      f'Processing paragraph {i + 1} of {len(paragraphs_raw)}...',
                                      90 + int((i + 1) / len(paragraphs_raw) * 10))
                
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
            
            yield self.emit_progress('story-generator', 'completed', 100, 'Story generation complete!', 100)
            
            return story_paragraphs[:paragraphs]
            
        except Exception as e:
            print(f"Error generating story: {str(e)}")
            yield self.emit_progress('story-generator', 'error', 0, f'Error: {str(e)}', None)
            return None
