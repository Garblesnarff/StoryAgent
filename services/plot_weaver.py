import groq
import os
import json
from typing import Dict, List, Optional

class PlotWeaver:
    def __init__(self):
        # Initialize Groq client
        self.client = groq.Groq(api_key=os.environ.get('GROQ_API_KEY'))

    def weave_plot(self, concept: Dict, world: Dict, genre: str, mood: str) -> Optional[Dict]:
        """Generate a detailed plot structure based on the story concept and world"""
        try:
            system_prompt = (
                f"You are a {genre} story plotting expert. Create a compelling plot structure "
                f"that maintains a {mood} atmosphere while incorporating the provided concept "
                "and world details."
            )

            user_prompt = (
                "Based on this concept and world:\n"
                f"Concept: {json.dumps(concept, indent=2)}\n"
                f"World: {json.dumps(world, indent=2)}\n\n"
                "Return a JSON object with these keys:\n"
                "- plot_outline (array of exactly 3 strings: beginning, middle, end)\n"
                "- key_events (array of exactly 4 strings: major plot points)\n"
                "- character_arcs (array of objects with name and development)\n"
                "- pacing_notes (string: guidance for story rhythm)\n"
                "Keep descriptions concise and impactful."
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
                raise Exception("No response from plot generation API")

            # Parse and validate JSON response
            plot_data = json.loads(response.choices[0].message.content)
            
            # Validate required fields
            required_fields = ['plot_outline', 'key_events', 'character_arcs', 'pacing_notes']
            if not all(field in plot_data for field in required_fields):
                raise Exception("Missing required fields in plot data")
                
            # Validate arrays
            if not isinstance(plot_data['plot_outline'], list) or len(plot_data['plot_outline']) != 3:
                raise Exception("Plot outline must be an array with exactly 3 elements")
            if not isinstance(plot_data['key_events'], list) or len(plot_data['key_events']) != 4:
                raise Exception("Key events must be an array with exactly 4 elements")
                
            return plot_data

        except Exception as e:
            print(f"Error weaving plot: {str(e)}")
            return None

    def develop_scenes(self, plot_data: Dict, world: Dict) -> Optional[Dict]:
        """Develop detailed scenes based on the plot structure"""
        try:
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
                "- scenes (array of objects with title, setting, and action)\n"
                "- transitions (array of strings connecting scenes)\n"
                "- emotional_beats (array of strings for key emotional moments)\n"
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
                raise Exception("No response from scene development API")

            scene_data = json.loads(response.choices[0].message.content)
            
            # Validate required fields
            required_fields = ['scenes', 'transitions', 'emotional_beats']
            if not all(field in scene_data for field in required_fields):
                raise Exception("Missing required fields in scene data")
                
            # Validate scene structure
            if not isinstance(scene_data['scenes'], list) or not scene_data['scenes']:
                raise Exception("Invalid scenes array")
                
            for scene in scene_data['scenes']:
                if not all(k in scene for k in ['title', 'setting', 'action']):
                    raise Exception("Invalid scene object structure")
            
            return scene_data

        except Exception as e:
            print(f"Error developing scenes: {str(e)}")
            return None

    def generate_dialogue(self, scene_data: Dict, characters: List[Dict]) -> Optional[Dict]:
        """Generate natural dialogue for key scenes"""
        try:
            system_prompt = (
                "You are a dialogue writing expert. Create natural, character-driven "
                "dialogue that advances the plot and reveals character personalities."
            )

            user_prompt = (
                "Based on these scenes and characters:\n"
                f"Scenes: {json.dumps(scene_data, indent=2)}\n"
                f"Characters: {json.dumps(characters, indent=2)}\n\n"
                "Return a JSON object with these keys:\n"
                "- dialogue_scenes (array of objects with scene_title and exchanges)\n"
                "- character_voices (object mapping character names to speech patterns)\n"
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
                raise Exception("No response from dialogue generation API")

            dialogue_data = json.loads(response.choices[0].message.content)
            
            # Validate required fields
            required_fields = ['dialogue_scenes', 'character_voices']
            if not all(field in dialogue_data for field in required_fields):
                raise Exception("Missing required fields in dialogue data")
                
            return dialogue_data

        except Exception as e:
            print(f"Error generating dialogue: {str(e)}")
            return None

    def refine_plot(self, plot_data: Dict, scene_data: Dict, dialogue_data: Dict) -> Optional[Dict]:
        """Refine and polish the complete plot structure"""
        try:
            system_prompt = (
                "You are a story editor specializing in plot refinement. Create a "
                "cohesive and engaging final plot structure that integrates all elements."
            )

            user_prompt = (
                "Based on these story elements:\n"
                f"Plot: {json.dumps(plot_data, indent=2)}\n"
                f"Scenes: {json.dumps(scene_data, indent=2)}\n"
                f"Dialogue: {json.dumps(dialogue_data, indent=2)}\n\n"
                "Return a JSON object with these keys:\n"
                "- refined_plot (array of detailed scene descriptions)\n"
                "- story_beats (array of emotional and plot points)\n"
                "- narrative_flow (string describing pacing and transitions)\n"
                "Focus on creating a seamless and engaging narrative."
            )

            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )

            if not response or not response.choices:
                raise Exception("No response from plot refinement API")

            refined_data = json.loads(response.choices[0].message.content)
            
            # Validate required fields
            required_fields = ['refined_plot', 'story_beats', 'narrative_flow']
            if not all(field in refined_data for field in required_fields):
                raise Exception("Missing required fields in refined plot data")
                
            return refined_data

        except Exception as e:
            print(f"Error refining plot: {str(e)}")
            return None
