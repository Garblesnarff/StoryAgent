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
                f"You are a {genre} world-building expert specializing in creating vivid "
                f"settings with a {mood} atmosphere. Focus on concise but evocative descriptions."
            )

            user_prompt = (
                "Based on this concept:\n"
                f"{json.dumps(concept, indent=2)}\n\n"
                "Return a JSON object with exactly these fields:\n"
                "- environment (string describing physical setting)\n"
                "- society (string describing social structure)\n"
                "- mood (array of exactly 3 strings)\n"
                "- sensory_details (array of exactly 3 strings)\n"
                "- locations (array of exactly 2 objects with name and description)\n\n"
                "Important: Follow this exact structure. No nested objects."
            )

            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=300,
                response_format={"type": "json_object"}
            )

            if not response or not response.choices:
                raise Exception("No response from world building API")

            # Parse and validate JSON response
            world_data = json.loads(response.choices[0].message.content)
            
            # Validate required fields
            required_fields = ['environment', 'society', 'mood', 'sensory_details', 'locations']
            missing_fields = [field for field in required_fields if field not in world_data]
            if missing_fields:
                raise Exception(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Validate array lengths
            if len(world_data['mood']) != 3:
                raise Exception("Mood array must contain exactly 3 elements")
            if len(world_data['sensory_details']) != 3:
                raise Exception("Sensory details array must contain exactly 3 elements")
            if len(world_data['locations']) != 2:
                raise Exception("Locations array must contain exactly 2 elements")
            
            # Validate location objects
            for loc in world_data['locations']:
                if not isinstance(loc, dict) or 'name' not in loc or 'description' not in loc:
                    raise Exception("Invalid location object structure")
            
            return world_data

        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            return self._get_fallback_world()
        except Exception as e:
            print(f"Error building world: {str(e)}")
            return self._get_fallback_world()

    def enhance_setting(self, world_data: Dict, genre: str) -> Optional[Dict]:
        """Add genre-specific enhancements to the world"""
        try:
            system_prompt = (
                f"You are a {genre} world-building expert. Enhance this existing world "
                "with exactly three rules and three unique elements."
            )

            user_prompt = (
                "Based on this world:\n"
                f"{json.dumps(world_data, indent=2)}\n\n"
                "Return a JSON object with exactly these fields:\n"
                "- environment (string describing physical setting)\n"
                "- society (string describing social structure)\n"
                "- rules (array of exactly 3 strings)\n"
                "- elements (array of exactly 3 strings)\n"
                "- atmosphere (object with mood and sensory_details arrays)\n\n"
                "Important: Follow this exact structure. No nested objects except for atmosphere."
            )

            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=300,
                response_format={"type": "json_object"}
            )

            if not response or not response.choices:
                raise Exception("No response from enhancement API")

            enhanced_data = json.loads(response.choices[0].message.content)
            return enhanced_data

        except Exception as e:
            print(f"Error enhancing setting: {str(e)}")
            return self._add_fallback_enhancements(world_data)

    def _get_fallback_world(self) -> Dict:
        """Return a simplified fallback world when generation fails"""
        return {
            'environment': 'A mysterious realm where ancient magic and modern technology coexist in delicate balance.',
            'society': 'A diverse community bound by ancient traditions and modern innovations.',
            'mood': ['mysterious', 'harmonious', 'dynamic'],
            'sensory_details': ['shimmering lights', 'humming machines', 'warm breezes'],
            'locations': [
                {
                    'name': 'The Grand Archive',
                    'description': 'A vast library where ancient scrolls and digital records are preserved.'
                },
                {
                    'name': 'The Nexus Plaza',
                    'description': 'A bustling marketplace where magic and technology traders gather.'
                }
            ]
        }

    def _add_fallback_enhancements(self, world_data: Dict) -> Dict:
        """Return fallback enhanced world when enhancement fails"""
        return {
            'environment': world_data.get('environment', 'A mysterious realm of endless possibilities'),
            'society': world_data.get('society', 'A complex web of relationships and traditions'),
            'rules': [
                'Magic follows the law of equivalent exchange',
                'Technology must respect natural balance',
                'Knowledge comes with responsibility'
            ],
            'elements': [
                'Ancient prophecies',
                'Mystical artifacts',
                'Hidden portals'
            ],
            'atmosphere': {
                'mood': world_data.get('mood', ['mysterious', 'harmonious', 'dynamic']),
                'sensory_details': world_data.get('sensory_details', ['shimmering lights', 'humming machines', 'warm breezes'])
            }
        }
