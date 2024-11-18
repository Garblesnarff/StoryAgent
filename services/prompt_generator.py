import google.generativeai as genai
import os
import logging

logger = logging.getLogger(__name__)

class PromptGenerator:
    def __init__(self):
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_image_prompt(self, story_context, paragraph_text):
        prompt = f'''
        Given the following story context and a specific paragraph, generate an artistic image prompt
        that captures the essence of the paragraph while maintaining consistency with the overall story.
        
        Story Context:
        {story_context}
        
        Current Paragraph:
        {paragraph_text}
        
        Generate a detailed image prompt that:
        1. Captures the key visual elements from the paragraph
        2. Maintains the story's atmosphere and tone
        3. Includes specific details about lighting, perspective, and mood
        4. Uses artistic and descriptive language
        '''
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating prompt: {str(e)}")
            return paragraph_text  # Fallback to paragraph text if generation fails
