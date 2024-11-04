import groq
import os
import json
from typing import Dict, Optional

class WorldBuilder:
    def __init__(self):
        # Initialize Groq client
        self.client = groq.Groq(api_key=os.environ.get('GROQ_API_KEY'))

    def build_world(self, concept: Dict, genre: str, mood: str) -> Optional[Dict]:
        """Generate a detailed world based on the story concept"""
        try:
            system_prompt = (
                "You are a world-building expert specializing in creating rich, "
                "detailed story settings. For each story concept, develop comprehensive "
                "world elements that enhance the narrative while maintaining consistency "
                "with the genre and mood."
            )

            user_prompt = (
                f"Create a detailed world for a {genre} story with a {mood} mood "
                f"based on this concept:\n{json.dumps(concept, indent=2)}\n\n"
                "Return a JSON object with these keys:\n"
                "- physical_environment (object with: geography, climate, architecture)\n"
                "- social_structure (object with: hierarchy, customs, beliefs)\n"
                "- world_history (object with: key_events, conflicts, developments)\n"
                "- atmosphere (object with: mood_elements, sensory_details)\n"
                "- world_rules (array of strings: fundamental laws/rules of this world)\n"
                "- locations (array of objects: key story locations with descriptions)"
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
                raise Exception("No response from world building API")

            world_data = json.loads(response.choices[0].message.content)
            
            # Validate the world data
            if not self.validate_world_data(world_data):
                raise Exception("Generated world data failed validation")

            return world_data

        except Exception as e:
            print(f"Error building world: {str(e)}")
            return None

    def validate_world_data(self, world_data: Dict) -> bool:
        """Validate if the world data contains all required elements"""
        try:
            required_fields = [
                'physical_environment', 'social_structure', 'world_history',
                'atmosphere', 'world_rules', 'locations'
            ]
            
            if not all(field in world_data for field in required_fields):
                return False

            # Validate nested structure
            nested_requirements = {
                'physical_environment': ['geography', 'climate', 'architecture'],
                'social_structure': ['hierarchy', 'customs', 'beliefs'],
                'world_history': ['key_events', 'conflicts', 'developments'],
                'atmosphere': ['mood_elements', 'sensory_details']
            }

            for field, subfields in nested_requirements.items():
                if not all(subfield in world_data[field] for subfield in subfields):
                    return False

            # Validate array fields
            if not isinstance(world_data['world_rules'], list) or \
               not isinstance(world_data['locations'], list):
                return False

            return True

        except Exception as e:
            print(f"Error validating world data: {str(e)}")
            return False

    def enhance_setting(self, world_data: Dict, genre: str) -> Optional[Dict]:
        """Add genre-specific enhancements to the world"""
        try:
            system_prompt = (
                f"You are a {genre} genre expert. Enhance the provided world with "
                "genre-specific elements while maintaining internal consistency."
            )

            user_prompt = (
                "Enhance this world with genre-specific details:\n"
                f"{json.dumps(world_data, indent=2)}\n\n"
                "Return a JSON object adding these keys:\n"
                "- genre_elements (array of unique genre features)\n"
                "- world_mechanics (how things work in this world)\n"
                "- distinctive_features (what makes this world unique)"
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
                raise Exception("No response from enhancement API")

            enhancements = json.loads(response.choices[0].message.content)
            
            # Merge enhancements with original world data
            world_data.update(enhancements)
            
            return world_data

        except Exception as e:
            print(f"Error enhancing setting: {str(e)}")
            return None
