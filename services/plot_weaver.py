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
        """Generate a simplified plot structure based on the story concept and world"""
        try:
            system_prompt = (
                f"You are a {genre} story plotting expert. Create a simplified plot "
                f"structure that maintains a {mood} atmosphere."
            )

            user_prompt = (
                "Based on this concept and world:\n"
                f"Concept: {json.dumps(concept, indent=2)}\n"
                f"World: {json.dumps(world, indent=2)}\n\n"
                "Return a JSON object with exactly these keys:\n"
                "- plot_points (array of exactly 5 strings describing key story events)\n"
                "- character_arcs (array of exactly 3 strings describing character development)\n"
                "- narrative_flow (string describing overall story progression)\n"
                "Keep all descriptions under 100 words each. No nested objects."
            )

            logger.info("Generating plot structure with Groq API")
            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=800,
                response_format={"type": "json_object"}
            )

            if not response or not response.choices:
                logger.error("No response received from Groq API")
                return self._get_fallback_plot()

            # Parse and validate JSON response
            plot_data = json.loads(response.choices[0].message.content)
            
            # Strict validation of required fields
            required_fields = ['plot_points', 'character_arcs', 'narrative_flow']
            missing_fields = [field for field in required_fields if field not in plot_data]
            if missing_fields:
                logger.error(f"Missing required fields in response: {missing_fields}")
                return self._get_fallback_plot()

            # Validate array lengths
            if not isinstance(plot_data['plot_points'], list) or len(plot_data['plot_points']) != 5:
                logger.error("Invalid plot_points array: must contain exactly 5 elements")
                return self._get_fallback_plot()

            if not isinstance(plot_data['character_arcs'], list) or len(plot_data['character_arcs']) != 3:
                logger.error("Invalid character_arcs array: must contain exactly 3 elements")
                return self._get_fallback_plot()

            if not isinstance(plot_data['narrative_flow'], str):
                logger.error("Invalid narrative_flow: must be a string")
                return self._get_fallback_plot()

            # Validate content lengths
            for idx, point in enumerate(plot_data['plot_points']):
                if not isinstance(point, str) or len(point) > 100:
                    logger.error(f"Invalid plot point {idx}: must be string under 100 words")
                    return self._get_fallback_plot()

            for idx, arc in enumerate(plot_data['character_arcs']):
                if not isinstance(arc, str) or len(arc) > 100:
                    logger.error(f"Invalid character arc {idx}: must be string under 100 words")
                    return self._get_fallback_plot()

            if len(plot_data['narrative_flow']) > 100:
                logger.error("Invalid narrative_flow: exceeds 100 words")
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
                "Main character discovers an unusual situation that disrupts their normal life",
                "Initial attempts to handle the situation lead to unexpected complications",
                "A crucial discovery reveals the true nature of the challenge",
                "Character faces a major setback that forces them to adapt",
                "Final confrontation leads to resolution and personal growth"
            ],
            'character_arcs': [
                "Protagonist evolves from hesitant observer to active participant",
                "Supporting character overcomes personal fears to aid the protagonist",
                "Antagonist's motivations are revealed, adding complexity to the conflict"
            ],
            'narrative_flow': "Story progresses from discovery through escalating challenges to ultimate resolution, maintaining tension while developing characters."
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
                    "Later that same day",
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
                        "Character 2: I'm not sure we can trust what we see.",
                        "Character 3: We need to keep moving forward."
                    ]
                }
                dialogue_scenes.append(dialogue_scene)

            return {
                'dialogue_scenes': dialogue_scenes,
                'character_voices': {
                    'Character 1': 'Determined and focused',
                    'Character 2': 'Cautious and analytical',
                    'Character 3': 'Supportive and optimistic'
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
                    "Inciting incident disrupts the status quo",
                    "Rising action builds tension",
                    "Climax brings all threads together",
                    "Resolution provides satisfying conclusion"
                ],
                'narrative_flow': plot_data['narrative_flow']
            }
        except Exception as e:
            logger.error(f"Error refining plot: {str(e)}")
            return None
