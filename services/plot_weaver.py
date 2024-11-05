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
            print("Plot Weaver: Starting plot structure generation...")
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
                model="gemma2-9b-it",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            if not response or not response.choices:
                print("Plot Weaver: Failed to generate plot structure")
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
            
            print("Plot Weaver: Successfully generated plot structure")
            return simplified_plot

        except Exception as e:
            print(f"Plot Weaver Error: {str(e)}")
            return {
                'plot_outline': ['Beginning', 'Middle', 'End'],
                'key_events': ['Introduction', 'Rising Action', 'Climax', 'Resolution'],
                'character_arcs': [{'name': 'Protagonist', 'development': 'Growth'}],
                'pacing_notes': 'Standard three-act structure'
            }

    def develop_scenes(self, plot_data: Dict, world: Dict) -> Optional[Dict]:
        """Develop detailed scenes based on the plot structure"""
        try:
            print("Plot Weaver: Starting scene development...")
            system_prompt = (
                "You are a scene development expert. Create concise scene descriptions "
                "that bring the plot to life while maintaining consistency with the "
                "world details. Keep all descriptions brief and focused."
            )

            user_prompt = (
                "Based on this plot and world:\n"
                f"Plot: {json.dumps(plot_data, indent=2)}\n"
                f"World: {json.dumps(world, indent=2)}\n\n"
                "Return a JSON object with exactly these fields:\n"
                "- scenes (array of exactly 3 objects with title and action fields)\n"
                "- transitions (array of exactly 3 strings)\n"
                "- emotional_beats (array of exactly 4 strings)\n"
                "Keep all descriptions under 50 words. No nested objects."
            )

            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",  # Use more reliable model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,  # Lower temperature for more consistent output
                max_tokens=800,
                response_format={"type": "json_object"}
            )

            if not response or not response.choices:
                raise Exception("No response from scene development API")

            scene_data = json.loads(response.choices[0].message.content)
            
            # Validate and fix the structure
            if not isinstance(scene_data.get('scenes', []), list):
                raise Exception("Invalid scenes structure")
                
            # Ensure exactly 3 scenes
            scene_data['scenes'] = scene_data.get('scenes', [])[:3]
            while len(scene_data['scenes']) < 3:
                scene_data['scenes'].append({
                    'title': f'Scene {len(scene_data["scenes"]) + 1}',
                    'action': 'Events unfold...'
                })
            
            # Ensure exactly 3 transitions
            scene_data['transitions'] = scene_data.get('transitions', [])[:3]
            while len(scene_data['transitions']) < 3:
                scene_data['transitions'].append(f'Transition {len(scene_data["transitions"]) + 1}')
            
            # Ensure exactly 4 emotional beats
            scene_data['emotional_beats'] = scene_data.get('emotional_beats', [])[:4]
            while len(scene_data['emotional_beats']) < 4:
                scene_data['emotional_beats'].append(f'Beat {len(scene_data["emotional_beats"]) + 1}')
            
            print("Plot Weaver: Successfully developed scenes")
            return scene_data

        except Exception as e:
            print(f"Plot Weaver Error: {str(e)}")
            # Return a simplified fallback structure
            return {
                'scenes': [
                    {'title': 'Opening', 'action': 'The story begins...'},
                    {'title': 'Conflict', 'action': 'Tension rises...'},
                    {'title': 'Resolution', 'action': 'The story concludes...'}
                ],
                'transitions': ['Beginning', 'Middle', 'End'],
                'emotional_beats': ['Hope', 'Fear', 'Struggle', 'Resolution']
            }

    def refine_plot(self, plot_data: Dict, scene_data: Dict, dialogue_data: Dict = None) -> Optional[Dict]:
        """Refine and polish the complete plot structure"""
        try:
            print("Plot Weaver: Starting plot refinement...")
            system_prompt = (
                "You are a story editor specializing in plot refinement. Create a "
                "cohesive and engaging final plot structure."
            )

            user_prompt = (
                "Based on these story elements:\n"
                f"Plot: {json.dumps(plot_data, indent=2)}\n"
                f"Scenes: {json.dumps(scene_data, indent=2)}\n"
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
                print("Plot Weaver: Failed to refine plot")
                raise Exception("No response from plot refinement API")

            refined_data = json.loads(response.choices[0].message.content)
            
            # Validate and simplify the structure
            simplified_refined = {
                'refined_plot': refined_data.get('refined_plot', [])[:5],
                'story_beats': refined_data.get('story_beats', [])[:4],
                'narrative_flow': refined_data.get('narrative_flow', '')
            }
            
            print("Plot Weaver: Successfully refined plot")
            return simplified_refined

        except Exception as e:
            print(f"Plot Weaver Error: {str(e)}")
            return {
                'refined_plot': ['Beginning', 'Middle', 'End'],
                'story_beats': ['Setup', 'Conflict', 'Climax', 'Resolution'],
                'narrative_flow': 'Classic three-act structure with rising tension'
            }
