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
            return None

    def theme_analysis(self, premise: Dict, genre: str) -> Dict:
        """Identify and validate core themes based on premise and genre"""
        try:
            system_prompt = (
                "You are a literary analyst specializing in theme identification and development. "
                "Analyze the given premise and genre to identify meaningful themes that resonate "
                "with the story's core elements while maintaining genre expectations."
            )

            user_prompt = (
                f"Analyze this premise for a {genre} story and identify its themes:\n"
                f"{json.dumps(premise, indent=2)}\n\n"
                "Return the analysis as a JSON object with these keys:\n"
                "- core_theme (primary theme)\n"
                "- supporting_themes (array of secondary themes)\n"
                "- thematic_elements (story elements that support themes)\n"
                "- theme_development (how themes could evolve)"
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

            theme_data = json.loads(response.choices[0].message.content)
            return theme_data

        except Exception as e:
            print(f"Error analyzing themes: {str(e)}")
            return None

    def conflict_generator(self, premise: Dict, theme: Dict) -> Dict:
        """Generate central conflicts based on premise and themes"""
        try:
            system_prompt = (
                "You are a story structure expert specializing in conflict development. "
                "Create compelling conflicts that drive the story forward while supporting "
                "the identified themes and premise."
            )

            user_prompt = (
                "Generate conflicts based on this premise and themes:\n"
                f"Premise: {json.dumps(premise, indent=2)}\n"
                f"Themes: {json.dumps(theme, indent=2)}\n\n"
                "Return the conflicts as a JSON object with these keys:\n"
                "- central_conflict (main story conflict)\n"
                "- internal_conflicts (character-based conflicts)\n"
                "- external_conflicts (situational conflicts)\n"
                "- conflict_progression (how conflicts evolve)"
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

            conflict_data = json.loads(response.choices[0].message.content)
            return conflict_data

        except Exception as e:
            print(f"Error generating conflicts: {str(e)}")
            return None

    def validate_concept(self, concept: Dict, genre: str, target_audience: str) -> bool:
        """Validate if the concept fits genre and audience requirements"""
        try:
            # Check required fields
            required_fields = ['core_theme', 'characters', 'setting', 'plot_points', 'emotional_journey']
            if not all(field in concept for field in required_fields):
                return False

            # Validate genre-specific elements
            genre_elements = {
                'fantasy': ['magical_elements', 'world_building'],
                'sci-fi': ['technological_elements', 'scientific_concepts'],
                'mystery': ['clues', 'suspense_elements'],
                'romance': ['relationship_development', 'emotional_arc'],
                'horror': ['tension_elements', 'fear_factors']
            }

            # Validate audience-appropriate content
            audience_requirements = {
                'children': ['age_appropriate', 'educational_value'],
                'young_adult': ['coming_of_age', 'relatable_conflicts'],
                'adult': ['complex_themes', 'mature_content']
            }

            # Check genre-specific requirements
            if genre in genre_elements:
                if not any(element in concept for element in genre_elements[genre]):
                    return False

            # Check audience-appropriate content
            if target_audience in audience_requirements:
                if not any(req in concept for req in audience_requirements[target_audience]):
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
                f"Create a detailed story concept based on:\n"
                f"Original Prompt: {prompt}\n"
                f"Premise: {json.dumps(premise, indent=2)}\n"
                f"Themes: {json.dumps(themes, indent=2)}\n"
                f"Conflicts: {json.dumps(conflicts, indent=2)}\n\n"
                "Return the concept as a JSON object with these keys:\n"
                "- core_theme\n"
                "- characters (array of character objects with name and description)\n"
                "- setting\n"
                "- plot_points (array with beginning, middle, and end)\n"
                "- emotional_journey\n"
                f"- {genre}_elements (genre-specific elements)\n"
                f"- {target_audience}_appropriate (audience-specific considerations)"
            )

            # Generate the concept using the llama model
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

            # Parse and validate the concept
            concept_data = json.loads(response.choices[0].message.content)
            
            if not self.validate_concept(concept_data, genre, target_audience):
                raise Exception("Generated concept failed validation")

            return concept_data

        except Exception as e:
            print(f"Error generating concept: {str(e)}")
            return None
