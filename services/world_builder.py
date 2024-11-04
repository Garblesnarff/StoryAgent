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
                f"You are a {genre} world-building expert. Create a simple but vivid world "
                f"that maintains a {mood} atmosphere. Focus on essential details only."
            )

            user_prompt = (
                "Based on this concept:\n"
                f"{json.dumps(concept, indent=2)}\n\n"
                "Return a JSON object with exactly these fields:\n"
                "{\n"
                "  'environment': string (brief physical description, max 50 words),\n"
                "  'society': string (brief social description, max 50 words),\n"
                "  'mood': array of exactly 3 mood descriptors,\n"
                "  'senses': array of exactly 3 sensory details,\n"
                "  'locations': array of exactly 2 objects with 'name' and 'description' fields\n"
                "}\n\n"
                "Important: Follow this exact structure. No additional fields."
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
            required_fields = ['environment', 'society', 'mood', 'senses', 'locations']
            missing_fields = [field for field in required_fields if field not in world_data]
            if missing_fields:
                raise Exception(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Validate array lengths
            if len(world_data['mood']) != 3:
                raise Exception("Mood array must contain exactly 3 elements")
            if len(world_data['senses']) != 3:
                raise Exception("Senses array must contain exactly 3 elements")
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
                f"You are a {genre} genre expert. Add essential genre elements "
                "while maintaining consistency with the existing world."
            )

            user_prompt = (
                "Enhance this world:\n"
                f"{json.dumps(world_data, indent=2)}\n\n"
                "Add exactly these fields to the JSON:\n"
                "{\n"
                "  'rules': array of exactly 3 strings (fundamental laws),\n"
                "  'elements': array of exactly 3 strings (unique genre features)\n"
                "}\n\n"
                "Important: Keep all existing fields unchanged."
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

            enhancements = json.loads(response.choices[0].message.content)
            
            # Validate enhancement fields
            required_fields = ['rules', 'elements']
            missing_fields = [field for field in required_fields if field not in enhancements]
            if missing_fields:
                raise Exception(f"Missing required enhancement fields: {', '.join(missing_fields)}")
            
            # Validate array lengths
            if len(enhancements['rules']) != 3:
                raise Exception("Rules array must contain exactly 3 elements")
            if len(enhancements['elements']) != 3:
                raise Exception("Elements array must contain exactly 3 elements")
            
            # Merge enhancements with original world data
            world_data.update(enhancements)
            return world_data

        except json.JSONDecodeError as e:
            print(f"JSON parsing error in enhancement: {str(e)}")
            return self._add_fallback_enhancements(world_data)
        except Exception as e:
            print(f"Error enhancing setting: {str(e)}")
            return self._add_fallback_enhancements(world_data)

    def _get_fallback_world(self) -> Dict:
        """Return a simplified fallback world when generation fails"""
        return {
            'environment': 'A mysterious realm where ancient magic and modern technology coexist in delicate balance.',
            'society': 'A diverse community bound by ancient traditions and modern innovations.',
            'mood': ['mysterious', 'harmonious', 'dynamic'],
            'senses': ['shimmering lights', 'humming machines', 'warm breezes'],
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
        """Add fallback enhancements to the world data"""
        world_data.update({
            'rules': [
                'Magic follows the law of equivalent exchange',
                'Technology must respect natural balance',
                'Knowledge comes with responsibility'
            ],
            'elements': [
                'Ancient prophecies',
                'Mystical artifacts',
                'Hidden portals'
            ]
        })
        return world_data
