import google.generativeai as genai
import os
import logging
from .langchain_prompt_manager import LangChainPromptManager

logger = logging.getLogger(__name__)

class PromptGenerator:
    def __init__(self):
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
        self.prompt_manager = LangChainPromptManager()

    def generate_image_prompt(self, story_context, paragraph_text, use_chain=True):
        try:
            if use_chain:
                # Generate chain of prompts for multi-step refinement
                prompts = self.prompt_manager.chain_prompts(
                    story_context=story_context,
                    paragraph_text=paragraph_text,
                    num_steps=3
                )
                return prompts
            else:
                # Use single-step prompt generation
                formatted_prompt = self.prompt_manager.format_image_prompt(
                    story_context=story_context,
                    paragraph_text=paragraph_text
                )
                response = self.model.generate_content(formatted_prompt)
                return [response.text.strip()]
        except Exception as e:
            logger.error(f"Error generating prompt: {str(e)}")
            return [paragraph_text]  # Fallback to paragraph text if generation fails
