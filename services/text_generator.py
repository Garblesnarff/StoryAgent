import groq
import os
import json

class TextGenerator:
    def __init__(self):
        # Initialize Groq client
        self.client = groq.Groq(api_key=os.environ.get('GROQ_API_KEY'))
    
    def generate_story(self, prompt, genre, mood, target_audience, paragraphs):
        try:
            # Adjust the system message based on the parameters and include sentence structure guidance
            system_message = f"""You are a creative storyteller specializing in {genre} stories with a {mood} mood for a {target_audience} audience. 
            Create coherent, well-structured sentences that can stand alone with proper context. Each sentence should be complete and meaningful on its own 
            while maintaining flow with surrounding content."""
            
            # Generate the story using Groq API
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Write a {genre} story with a {mood} mood for a {target_audience} audience based on this prompt: {prompt}. The story should be exactly {paragraphs} paragraphs long."}
                ],
                temperature=0.7,
            )
            
            if not response or not response.choices:
                raise Exception("No response from story generation API")
                
            story = response.choices[0].message.content
            if not story:
                raise Exception("Empty response from story generation API")
            
            # Split the story into paragraphs
            story_paragraphs = [p for p in story.split('\n\n') if p.strip()][:paragraphs]
            
            return story_paragraphs
            
        except Exception as e:
            print(f"Error generating story: {str(e)}")
            return None
