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
            # Generate story text with improved prompt
            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": f"You are a creative storyteller specializing in {genre} stories with a {mood} mood for a {target_audience} audience. Write a story in a natural flowing narrative style."},
                    {"role": "user", "content": f"Write a {genre} story with a {mood} mood for a {target_audience} audience based on this prompt: {prompt}. Write it as {paragraphs} distinct paragraphs, where each paragraph naturally flows and contains approximately 2-3 sentences. Do not include any segment markers or labels."}
                ],
                temperature=0.7,
            )
            
            if not response or not response.choices:
                raise Exception("No response from story generation API")
                
            story = response.choices[0].message.content
            if not story:
                raise Exception("Empty response from story generation API")
            
            # Split story into paragraphs, cleaned of any potential markers
            paragraphs_raw = story.split('\n\n')
            story_paragraphs = []
            
            for paragraph in paragraphs_raw:
                # Clean the paragraph of any numbering or markers
                cleaned = re.sub(r'^[0-9]+[\.\)]\s*', '', paragraph.strip())
                cleaned = re.sub(r'Segment\s*[0-9]+:?\s*', '', cleaned)
                
                if cleaned:
                    story_paragraphs.append(cleaned)
                    
            return story_paragraphs[:paragraphs]
            
        except Exception as e:
            print(f"Error generating story: {str(e)}")
            return None
