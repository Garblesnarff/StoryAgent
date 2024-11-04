import groq
import os
import json
from typing import Dict, List, Optional

class ConceptGenerator:
    def __init__(self):
        # Initialize Groq client
        self.client = groq.Groq(api_key=os.environ.get('GROQ_API_KEY'))

    def generate_premise(self, genre: str, target_audience: str) -> Dict:
        """Generate unique premises and hooks for a story"""
        try:
            system_prompt = (
                "You are a creative writing expert specializing in generating unique story premises. "
                "For each genre and audience combination, create compelling hooks and premises that "
                "will engage the target audience while staying true to genre conventions."
            )

            user_prompt = (
                f"Generate a unique story premise for a {genre} story targeting a {target_audience} audience.\n"
                "Return the premise as a JSON object with these keys:\n"
                "- hook (attention-grabbing opening concept)\n"
                "- premise (main story idea)\n"
                "- unique_elements (array of distinctive story elements)\n"
                "- target_themes (potential themes to explore)"
            )

            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            if not response or not response.choices:
                raise Exception("No response from premise generation API")

            premise_data = json.loads(response.choices[0].message.content)
            return premise_data

        except Exception as e:
            print(f"Error generating premise: {str(e)}")
            return {
                'hook': 'A unique discovery changes everything',
                'premise': 'A character faces an extraordinary challenge',
                'unique_elements': ['Mystery element', 'Personal growth', 'Unexpected twist'],
                'target_themes': ['Discovery', 'Transformation', 'Resilience']
            }

    def theme_analysis(self, premise: Dict, genre: str) -> Dict:
        try:
            system_prompt = (
                "You are a literary analyst specializing in theme identification. "
                "Analyze the given premise and genre to identify core themes that "
                "resonate with the story while maintaining genre expectations."
            )

            user_prompt = (
                f"Analyze this premise for a {genre} story and identify its themes:\n"
                f"{json.dumps(premise, indent=2)}\n\n"
                "Return a simplified JSON object with these keys:\n"
                "- core_theme (string: primary theme)\n"
                "- supporting_themes (array of strings: secondary themes)\n"
                "- thematic_elements (array of strings: key story elements)\n"
                "- theme_development (string: brief description of theme progression)"
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
                raise Exception("No response from theme analysis API")

            theme_data = json.loads(response.choices[0].message.content)
            
            # Validate required fields
            required_fields = ['core_theme', 'supporting_themes', 'thematic_elements', 'theme_development']
            if not all(field in theme_data for field in required_fields):
                raise Exception("Missing required fields in theme analysis response")
                
            return theme_data

        except Exception as e:
            print(f"Error analyzing themes: {str(e)}")
            return {
                'core_theme': 'Growth and Change',
                'supporting_themes': ['Perseverance', 'Self-discovery'],
                'thematic_elements': ['Character development', 'Obstacles to overcome'],
                'theme_development': 'Progression from challenge to resolution'
            }

    def conflict_generator(self, premise: Dict, theme: Dict) -> Dict:
        """Generate central conflicts based on premise and themes"""
        try:
            system_prompt = (
                "You are a story structure expert specializing in conflict development. "
                "Create compelling conflicts that drive the story forward while supporting "
                "the identified themes and premise."
            )

            user_prompt = (
                "Based on the provided premise and themes, generate a JSON object with these keys:\n"
                "- central_conflict (string: main story conflict)\n"
                "- internal_conflicts (array of strings: character-based conflicts)\n"
                "- external_conflicts (array of strings: situational conflicts)\n"
                "- conflict_progression (string: brief description of how conflicts evolve)\n\n"
                f"Premise: {json.dumps(premise, indent=2)}\n"
                f"Themes: {json.dumps(theme, indent=2)}"
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
                raise Exception("No response from conflict generation API")

            conflict_data = json.loads(response.choices[0].message.content)
            
            # Validate required fields
            required_fields = ['central_conflict', 'internal_conflicts', 'external_conflicts', 'conflict_progression']
            if not all(field in conflict_data for field in required_fields):
                raise Exception("Missing required fields in conflict generation response")
            
            return conflict_data

        except Exception as e:
            print(f"Error generating conflicts: {str(e)}")
            return {
                'central_conflict': 'Character vs Unknown',
                'internal_conflicts': ['Self-doubt', 'Fear of failure'],
                'external_conflicts': ['Environmental challenges', 'Opposition from others'],
                'conflict_progression': 'Escalating challenges lead to personal transformation'
            }

    def validate_concept(self, concept: Dict, genre: str, target_audience: str) -> bool:
        """Validate if the concept fits genre and audience requirements"""
        try:
            # Check required fields
            required_fields = ['core_theme', 'characters', 'setting', 'plot_points', 'emotional_journey']
            if not all(field in concept for field in required_fields):
                return False

            return True

        except Exception as e:
            print(f"Error validating concept: {str(e)}")
            return False

    def generate_concept(self, prompt: str, genre: str, mood: str, target_audience: str) -> Optional[Dict]:
        """Generate complete story concept with enhanced genre and audience handling"""
        try:
            # Generate initial premise
            premise = self.generate_premise(genre, target_audience)
            if not premise:
                raise Exception("Failed to generate premise")

            # Analyze themes
            themes = self.theme_analysis(premise, genre)
            if not themes:
                raise Exception("Failed to analyze themes")

            # Generate conflicts
            conflicts = self.conflict_generator(premise, themes)
            if not conflicts:
                raise Exception("Failed to generate conflicts")

            # Create a detailed system prompt for concept generation
            system_prompt = (
                "You are a creative writing assistant specializing in generating detailed story concepts. "
                f"Create a {genre} story concept that maintains a {mood} mood and is appropriate for a {target_audience} audience. "
                "Incorporate the provided premise, themes, and conflicts into a cohesive concept."
            )

            # Create the user prompt combining all elements
            user_prompt = (
                "Create a detailed story concept based on:\n"
                f"Original Prompt: {prompt}\n"
                f"Premise: {json.dumps(premise)}\n"
                f"Themes: {json.dumps(themes)}\n"
                f"Conflicts: {json.dumps(conflicts)}\n\n"
                "Return a JSON object with these keys:\n"
                "- core_theme (string)\n"
                "- characters (array of objects with name and description)\n"
                "- setting (string)\n"
                "- plot_points (array of strings: beginning, middle, end)\n"
                "- emotional_journey (string)"
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
                raise Exception("No response from concept generation API")

            concept_data = json.loads(response.choices[0].message.content)
            
            if not self.validate_concept(concept_data, genre, target_audience):
                raise Exception("Generated concept failed validation")

            return concept_data

        except Exception as e:
            print(f"Error generating concept: {str(e)}")
            return None
