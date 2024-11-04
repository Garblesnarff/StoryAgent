import groq
import os
import json
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlotWeaver:
    def __init__(self):
        # Initialize Groq client
        self.client = groq.Groq(api_key=os.environ.get('GROQ_API_KEY'))

    def weave_plot(self, concept: Dict, world: Dict, genre: str, mood: str) -> Optional[Dict]:
        try:
            system_prompt = (
                f"You are a {genre} story plotting expert. Create a concise plot "
                f"structure that maintains a {mood} mood. Keep all descriptions short and focused."
            )

            user_prompt = (
                "Based on this concept and world:\n"
                f"Concept: {json.dumps(concept, indent=2)}\n"
                f"World: {json.dumps(world, indent=2)}\n\n"
                "Return a JSON object with exactly these fields:\n"
                "- plot_points (array of exactly 3 strings, each under 50 words)\n"
                "- character_arcs (array of exactly 2 strings, each under 50 words)\n"
                "- narrative_flow (string under 50 words)\n\n"
                "Keep responses extremely concise. Focus on key events only."
            )

            logger.info("Generating plot structure with Groq API")
            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=400,
                response_format={"type": "json_object"}
            )

            if not response or not response.choices:
                logger.error("No response received from Groq API")
                return self._get_fallback_plot()

            # Parse and validate JSON response
            plot_data = json.loads(response.choices[0].message.content)
            
            # Strict validation with word count
            def count_words(text: str) -> int:
                return len(text.split())
            
            # Validate plot points
            if not isinstance(plot_data.get('plot_points'), list) or len(plot_data['plot_points']) != 3:
                logger.error("plot_points must be array of exactly 3 strings")
                return self._get_fallback_plot()
            for point in plot_data['plot_points']:
                if not isinstance(point, str) or count_words(point) > 50:
                    logger.error("Each plot point must be string under 50 words")
                    return self._get_fallback_plot()
                
            # Validate character arcs
            if not isinstance(plot_data.get('character_arcs'), list) or len(plot_data['character_arcs']) != 2:
                logger.error("character_arcs must be array of exactly 2 strings")
                return self._get_fallback_plot()
            for arc in plot_data['character_arcs']:
                if not isinstance(arc, str) or count_words(arc) > 50:
                    logger.error("Each character arc must be string under 50 words")
                    return self._get_fallback_plot()
                
            # Validate narrative flow
            if not isinstance(plot_data.get('narrative_flow'), str) or count_words(plot_data['narrative_flow']) > 50:
                logger.error("narrative_flow must be string under 50 words")
                return self._get_fallback_plot()

            logger.info("Successfully generated and validated plot structure")
            return plot_data

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return self._get_fallback_plot()
        except Exception as e:
            logger.error(f"Error weaving plot: {str(e)}")
            return self._get_fallback_plot()

    def _get_fallback_plot(self) -> Dict:
        """Return a simplified fallback plot when generation fails"""
        return {
            'plot_points': [
                "Main character discovers an unusual situation in their everyday life.",
                "Complications arise as they try to handle the situation.",
                "Final confrontation leads to personal growth and resolution."
            ],
            'character_arcs': [
                "Protagonist evolves from hesitant observer to confident leader.",
                "Supporting character overcomes fears to help the protagonist."
            ],
            'narrative_flow': "Story progresses from discovery through challenges to resolution."
        }

    def develop_scenes(self, plot_data: Dict, world: Dict) -> Optional[Dict]:
        """Develop detailed scenes based on the plot structure"""
        try:
            # Convert plot points into detailed scenes
            scenes = []
            for i, plot_point in enumerate(plot_data['plot_points']):
                scene = {
                    'title': f"Scene {i+1}",
                    'setting': world.get('setting', 'A mysterious location'),
                    'action': plot_point
                }
                scenes.append(scene)

            return {
                'scenes': scenes,
                'transitions': [
                    "Time passes as tension builds",
                    "Meanwhile, in another location",
                    "As events unfold"
                ],
                'emotional_beats': [
                    "Hope turns to uncertainty",
                    "Fear gives way to determination",
                    "Triumph emerges from despair"
                ]
            }
        except Exception as e:
            logger.error(f"Error developing scenes: {str(e)}")
            return None

    def generate_dialogue(self, scene_data: Dict, characters: List[Dict]) -> Optional[Dict]:
        """Generate simplified dialogue for key scenes"""
        try:
            dialogue_scenes = []
            for scene in scene_data.get('scenes', []):
                dialogue_scene = {
                    'scene_title': scene['title'],
                    'exchanges': [
                        "Character 1: Let's figure this out together.",
                        "Character 2: We need to stay focused and move forward."
                    ]
                }
                dialogue_scenes.append(dialogue_scene)

            return {
                'dialogue_scenes': dialogue_scenes,
                'character_voices': {
                    'Character 1': 'Determined and focused',
                    'Character 2': 'Supportive and practical'
                }
            }
        except Exception as e:
            logger.error(f"Error generating dialogue: {str(e)}")
            return None

    def refine_plot(self, plot_data: Dict, scene_data: Dict, dialogue_data: Dict) -> Optional[Dict]:
        """Create a simplified refined plot structure"""
        try:
            return {
                'refined_plot': plot_data['plot_points'],
                'story_beats': [
                    "Opening establishes the normal world",
                    "Complications challenge the protagonist",
                    "Resolution brings transformation"
                ],
                'narrative_flow': plot_data['narrative_flow']
            }
        except Exception as e:
            logger.error(f"Error refining plot: {str(e)}")
            return None
