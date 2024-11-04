import groq
import os
import json
from typing import Dict, List, Optional

class ConceptGenerator:
    def __init__(self):
        # Initialize Groq client
        self.client = groq.Groq(api_key=os.environ.get('GROQ_API_KEY'))

    def generate_concept(self, prompt: str, genre: str, mood: str, target_audience: str) -> Optional[Dict]:
        """
        Generate creative story concepts using llama-3.1-70b-versatile model
        Returns a dictionary containing expanded story elements and suggestions
        """
        try:
            # Create a detailed system prompt for concept generation
            system_prompt = (
                "You are a creative writing assistant specializing in generating detailed story concepts. "
                "For each prompt, provide a structured story concept with these elements:\n"
                "1. Core Theme - The central message or idea\n"
                "2. Character Profiles - Brief descriptions of main characters\n"
                "3. Setting Details - Rich description of the world/environment\n"
                "4. Plot Points - Key story beats in a 3-act structure\n"
                "5. Emotional Journey - The emotional arc of the story\n"
                "Format the response as structured JSON."
            )

            # Create the user prompt combining all inputs
            user_prompt = (
                f"Create a detailed story concept for a {genre} story with a {mood} mood "
                f"aimed at a {target_audience} audience, based on this prompt: {prompt}\n\n"
                "Return the concept as a JSON object with these keys:\n"
                "- core_theme\n"
                "- characters (array of character objects with name and description)\n"
                "- setting\n"
                "- plot_points (array with beginning, middle, and end)\n"
                "- emotional_journey"
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
                top_p=0.9,
                response_format={"type": "json_object"}
            )

            if not response or not response.choices:
                raise Exception("No response from concept generation API")

            # Parse the JSON response
            concept_text = response.choices[0].message.content
            concept_data = json.loads(concept_text)

            # Validate the required fields
            required_fields = ['core_theme', 'characters', 'setting', 'plot_points', 'emotional_journey']
            if not all(field in concept_data for field in required_fields):
                raise Exception("Missing required fields in concept generation response")

            return concept_data

        except Exception as e:
            print(f"Error generating concept: {str(e)}")
            return None

    def refine_concept(self, concept: Dict, feedback: str) -> Optional[Dict]:
        """
        Refine an existing concept based on feedback
        """
        try:
            # Create a system prompt for concept refinement
            system_prompt = (
                "You are a creative writing assistant helping to refine story concepts. "
                "Analyze the existing concept and the feedback, then provide an improved version "
                "that addresses the feedback while maintaining the story's core elements."
            )

            # Create the user prompt for refinement
            user_prompt = (
                f"Please refine this story concept based on the following feedback: {feedback}\n\n"
                f"Current concept: {json.dumps(concept, indent=2)}\n\n"
                "Return the refined concept as a JSON object with the same structure."
            )

            # Generate the refined concept
            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9,
                response_format={"type": "json_object"}
            )

            if not response or not response.choices:
                raise Exception("No response from concept refinement API")

            # Parse the JSON response
            refined_concept = json.loads(response.choices[0].message.content)
            return refined_concept

        except Exception as e:
            print(f"Error refining concept: {str(e)}")
            return None
