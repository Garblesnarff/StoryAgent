import groq
import os
import json
import re

class TextGenerator:
    def __init__(self):
        # Initialize Groq client
        self.client = groq.Groq(api_key=os.environ.get('GROQ_API_KEY'))
    
    def generate_story(self, prompt, genre, mood, target_audience, paragraphs):
        try:
            # Generate story text as before
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": f"You are a creative storyteller specializing in {genre} stories with a {mood} mood for a {target_audience} audience. Write a story as a series of 2-sentence segments."},
                    {"role": "user", "content": f"Write a {genre} story with a {mood} mood for a {target_audience} audience based on this prompt: {prompt}. Format the story as {paragraphs} segments, with exactly 2 sentences per segment."}
                ],
                temperature=0.7,
            )
            
            if not response or not response.choices:
                raise Exception("No response from story generation API")
                
            story = response.choices[0].message.content
            if not story:
                raise Exception("Empty response from story generation API")
            
            # Split story into 2-sentence segments
            sentences = re.split(r'(?<=[.!?])\s+', story)
            story_segments = []
            
            for i in range(0, len(sentences), 2):
                if i + 1 < len(sentences):
                    segment = sentences[i] + ' ' + sentences[i + 1]
                    story_segments.append(segment)
                elif i < len(sentences):
                    # Handle odd number of sentences by keeping the last one
                    story_segments.append(sentences[i])
                    
            return story_segments[:paragraphs]
            
        except Exception as e:
            print(f"Error generating story: {str(e)}")
            return None
