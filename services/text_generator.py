import groq
import os
import json

class TextGenerator:
    def __init__(self):
        # Initialize Groq client
        self.client = groq.Groq(api_key=os.environ.get('GROQ_API_KEY'))
    
    def generate_story(self, prompt, genre, mood, target_audience, paragraphs):
        try:
            # Adjust the system message based on the parameters
            system_message = f"You are a creative storyteller specializing in {genre} stories with a {mood} mood for a {target_audience} audience. Write a story based on the given prompt."
            
            # Generate the story using Groq API
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Write a {genre} story with a {mood} mood for a {target_audience} audience based on this prompt: {prompt}. The story should be natural and flowing, with approximately {paragraphs} sentences."}
                ],
                temperature=0.7,
            )
            
            if not response or not response.choices:
                raise Exception("No response from story generation API")
                
            story = response.choices[0].message.content
            if not story:
                raise Exception("Empty response from story generation API")
            
            # Split into sentences instead of paragraphs
            # Split on ., !, and ? followed by a space
            sentences = [s.strip() + '.' for s in story.replace('!', '.').replace('?', '.').split('.') if s.strip()]
            
            # Limit to requested number of sentences
            return sentences[:paragraphs]
            
        except Exception as e:
            print(f"Error generating story: {str(e)}")
            return None
