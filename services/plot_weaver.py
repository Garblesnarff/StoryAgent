import groq
import os
import json
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlotWeaver:
    def __init__(self):
        # Initialize Groq client
        self.client = groq.Groq(api_key=os.environ.get('GROQ_PLOT_API_KEY'))

    def weave_plot(self, concept: Dict, world: Dict, genre: str, mood: str) -> Optional[Dict]:
        """Generate a detailed plot structure based on the story concept and world"""
        try:
            logger.info("Plot Weaver: Starting plot structure generation...")
            system_prompt = (
                f"You are a {genre} story plotting expert. Create a simple plot structure "
                f"that maintains a {mood} atmosphere. Focus on key story elements only."
            )

            user_prompt = (
                "Based on this concept and world:\n"
                f"Concept: {json.dumps(concept, indent=2)}\n"
                f"World: {json.dumps(world, indent=2)}\n\n"
                "Return a simple JSON object with these exact fields:\n"
                "- plot_outline (array of exactly 3 strings: beginning, middle, end)\n"
                "- key_events (array of exactly 4 key plot points)\n"
                "- character_arcs (array of objects with name and development fields)\n"
                "- pacing_notes (string describing story rhythm)\n"
                "Keep all descriptions under 100 words. No nested objects beyond character_arcs."
            )

            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            if not response or not response.choices:
                logger.error("Plot Weaver: Failed to generate plot structure")
                raise Exception("No response from plot generation API")

            plot_data = json.loads(response.choices[0].message.content)
            
            # Validate and simplify the response structure
            simplified_plot = {
                'plot_outline': plot_data.get('plot_outline', [])[:3],
                'key_events': plot_data.get('key_events', [])[:4],
                'character_arcs': [
                    {'name': arc.get('name', ''), 'development': arc.get('development', '')}
                    for arc in plot_data.get('character_arcs', [])[:3]
                ],
                'pacing_notes': plot_data.get('pacing_notes', 'Standard three-act structure')
            }
            
            # Validate the simplified structure
            if len(simplified_plot['plot_outline']) != 3:
                raise Exception("Invalid plot outline structure")
            if len(simplified_plot['key_events']) != 4:
                raise Exception("Invalid key events structure")
            if not simplified_plot['character_arcs']:
                raise Exception("Missing character arcs")
            
            logger.info("Plot Weaver: Successfully generated plot structure")
            return simplified_plot

        except Exception as e:
            logger.error(f"Plot Weaver Error: {str(e)}")
            return None

    def develop_scenes(self, plot_data: Dict, world: Dict) -> Optional[Dict]:
        """Develop detailed scenes based on the plot structure"""
        try:
            logger.info("Plot Weaver: Starting scene development...")
            system_prompt = (
                "You are a scene development expert. Create vivid scene descriptions "
                "that bring the plot to life while maintaining consistency with the "
                "world details."
            )

            user_prompt = (
                "Based on this plot and world:\n"
                f"Plot: {json.dumps(plot_data, indent=2)}\n"
                f"World: {json.dumps(world, indent=2)}\n\n"
                "Return a JSON object with these keys:\n"
                "- scenes (array of objects with title and action)\n"
                "- transitions (array of strings connecting scenes)\n"
                "- emotional_beats (array of key emotional moments)\n"
                "Keep scene descriptions under 100 words each."
            )

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
                logger.error("Plot Weaver: Failed to develop scenes")
                raise Exception("No response from scene development API")

            scene_data = json.loads(response.choices[0].message.content)
            
            # Validate required fields
            required_fields = ['scenes', 'transitions', 'emotional_beats']
            if not all(field in scene_data for field in required_fields):
                logger.error("Plot Weaver: Missing required fields in scene data")
                raise Exception("Missing required fields in scene data")
            
            logger.info("Plot Weaver: Successfully developed scenes")
            return scene_data

        except Exception as e:
            logger.error(f"Plot Weaver Error: {str(e)}")
            return None

    def generate_dialogue(self, scenes: Dict, characters: List[Dict]) -> Optional[Dict]:
        """Generate dialogue for the scenes"""
        try:
            logger.info("Plot Weaver: Starting dialogue generation...")
            system_prompt = (
                "You are a dialogue expert. Create natural, character-driven dialogue "
                "that advances the plot and reveals character personalities."
            )

            user_prompt = (
                "Based on these scenes and characters:\n"
                f"Scenes: {json.dumps(scenes, indent=2)}\n"
                f"Characters: {json.dumps(characters, indent=2)}\n\n"
                "Return a JSON object with these keys:\n"
                "- dialogues (array of objects with scene_id, speaker, and line)\n"
                "Keep dialogue natural and impactful."
            )

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
                logger.error("Plot Weaver: Failed to generate dialogue")
                raise Exception("No response from dialogue generation API")

            dialogue_data = json.loads(response.choices[0].message.content)
            logger.info("Plot Weaver: Successfully generated dialogue")
            return dialogue_data

        except Exception as e:
            logger.error(f"Plot Weaver Error: {str(e)}")
            return None

    def refine_plot(self, plot_data: Dict, scene_data: Dict, dialogue_data: Dict = None) -> Optional[Dict]:
        """Refine and polish the complete plot structure"""
        try:
            logger.info("Plot Weaver: Starting plot refinement...")
            system_prompt = (
                "You are a story editor specializing in plot refinement. Create a "
                "cohesive and engaging final plot structure."
            )

            user_prompt = (
                "Based on these story elements:\n"
                f"Plot: {json.dumps(plot_data, indent=2)}\n"
                f"Scenes: {json.dumps(scene_data, indent=2)}\n"
                f"Dialogue: {json.dumps(dialogue_data, indent=2) if dialogue_data else '{}'}\n\n"
                "Return a JSON object with these keys:\n"
                "- refined_plot (array of scene descriptions)\n"
                "- story_beats (array of key moments)\n"
                "- narrative_flow (string describing pacing)\n"
                "Keep descriptions concise."
            )

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
                logger.error("Plot Weaver: Failed to refine plot")
                raise Exception("No response from plot refinement API")

            refined_data = json.loads(response.choices[0].message.content)
            
            # Validate and simplify the structure
            simplified_refined = {
                'refined_plot': refined_data.get('refined_plot', [])[:5],
                'story_beats': refined_data.get('story_beats', [])[:4],
                'narrative_flow': refined_data.get('narrative_flow', '')
            }
            
            logger.info("Plot Weaver: Successfully refined plot")
            return simplified_refined

        except Exception as e:
            logger.error(f"Plot Weaver Error: {str(e)}")
            return None
