import google.generativeai as genai
import os
import logging
import time
from database import db
from models import PromptMetric

logger = logging.getLogger(__name__)

class PromptGenerator:
    def __init__(self):
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')

    def _record_metrics(self, prompt_type, generation_time, num_steps, success, cache_hit=False, prompt_length=0, error_msg=None):
        """Record prompt generation metrics"""
        try:
            metric = PromptMetric(
                prompt_type=prompt_type,
                generation_time=generation_time,
                num_refinement_steps=num_steps,
                success=success,
                cache_hit=cache_hit,
                prompt_length=prompt_length,
                error_message=error_msg
            )
            db.session.add(metric)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error recording metrics: {str(e)}")

    def _format_image_prompt(self, story_context, paragraph_text):
        """Format prompt for image generation"""
        return f"""
        Create a detailed image generation prompt based on the following paragraph.
        Focus on visual elements and concrete details. Do not use overly abstract or flowery language.

        Paragraph:
        {paragraph_text}
        """

    def generate_image_prompt(self, story_context, paragraph_text, use_chain=True):
        start_time = time.time()
        success = False
        error_msg = None
        num_steps = 1
        prompt_length = len(story_context) + len(paragraph_text)

        try:
            if use_chain:
                # Multi-step prompt refinement
                prompts = []
                base_prompt = self._format_image_prompt(story_context, paragraph_text)
                current_prompt = base_prompt
                num_steps = 2  # Reduced from 3

                for step in range(num_steps):
                    response = self.model.generate_content(current_prompt)
                    refined_prompt = response.text.strip()
                    prompts.append(refined_prompt)

                    if step < num_steps - 1:
                        current_prompt = f"""
                        Refine the following image prompt to be more concise and focused on concrete visual details:
                        {refined_prompt}
                        """

                success = True
                return prompts[-1:]
            else:
                # Single-step prompt generation
                formatted_prompt = self._format_image_prompt(story_context, paragraph_text)
                response = self.model.generate_content(formatted_prompt)
                success = True
                return [response.text.strip()]

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating prompt: {error_msg}")
            return [paragraph_text]  # Fallback to paragraph text

        finally:
            generation_time = time.time() - start_time
            self._record_metrics(
                prompt_type='image',
                generation_time=generation_time,
                num_steps=num_steps,
                success=success,
                prompt_length=prompt_length,
                error_msg=error_msg
            )