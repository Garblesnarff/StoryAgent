import groq
import os
import json
from typing import Dict, Optional

class WorldBuilder:
    def __init__(self):
        # Initialize Groq client
        self.client = groq.Groq(api_key=os.environ.get('GROQ_WORLD_API_KEY'))

    def build_world(self, concept: Dict, genre: str, mood: str) -> Optional[Dict]:
        """Generate a detailed world based on the story concept"""
        try:
            system_prompt = (
                f"You are a {genre} world-building expert. Create a concise but vivid "
                f"world that maintains a {mood} atmosphere. Focus on essential details only."
            )

            user_prompt = (
                "Based on this concept:\n"
                f"{json.dumps(concept, indent=2)}\n\n"
                "Return a JSON object with exactly these fields:\n"
                "- setting (string: physical description under 100 words)\n"
                "- atmosphere (string: mood description under 50 words)\n"
                "- locations (array of exactly 2 objects with name and description)\n"
                "Keep descriptions concise and vivid. No nested objects."
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
            required_fields = ['setting', 'atmosphere', 'locations']
            missing_fields = [field for field in required_fields if field not in world_data]
            if missing_fields:
                raise Exception(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Validate location objects
            if not isinstance(world_data['locations'], list) or len(world_data['locations']) != 2:
                raise Exception("Locations must be an array with exactly 2 elements")
                
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
                f"You are a {genre} world-building expert. Create a concise but vivid "
                "enhanced world description with the following structure."
            )

            user_prompt = (
                "Based on this world:\n"
                f"{json.dumps(world_data, indent=2)}\n\n"
                "Return a JSON object with these exact fields:\n"
                "- setting (string: a single paragraph physical description)\n"
                "- atmosphere (string: a brief mood description)\n"
                "- rules (array of exactly 3 strings: fundamental laws of this world)\n"
                "Keep all descriptions under 100 words each. No nested objects."
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
            
            # Validate the structure
            if not all(k in enhanced_data for k in ['setting', 'atmosphere', 'rules']):
                raise Exception("Invalid response structure")
            if not isinstance(enhanced_data['rules'], list) or len(enhanced_data['rules']) != 3:
                raise Exception("Invalid rules array")
                
            return enhanced_data

        except Exception as e:
            print(f"Error enhancing setting: {str(e)}")
            # Return a simplified fallback
            return {
                'setting': 'A mysterious realm where magic and technology coexist.',
                'atmosphere': 'An air of mystery and wonder pervades the environment.',
                'rules': [
                    'Magic follows natural laws',
                    'Technology enhances natural abilities',
                    'Balance must be maintained'
                ]
            }

    def _get_fallback_world(self) -> Dict:
        """Return a simplified fallback world when generation fails"""
        return {
            'setting': 'A mysterious realm where ancient magic and modern technology coexist in delicate balance.',
            'atmosphere': 'An air of mystery and wonder pervades this timeless place.',
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
