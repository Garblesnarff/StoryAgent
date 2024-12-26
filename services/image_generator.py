
from typing import Dict, List, Optional
import time
import os
import logging
from datetime import datetime, timedelta
from collections import deque
from together import Together

logger = logging.getLogger(__name__)

class ImageGenerator:
    def __init__(self):
        self.client = Together(api_key=os.environ.get('TOGETHER_AI_API_KEY'))
        self.image_generation_queue = deque(maxlen=6)
        self.IMAGE_RATE_LIMIT = 60  # 60 seconds (1 minute)

    def _style_to_prompt_modifier(self, text: str, style: str = 'realistic') -> str:
        """Convert style parameter to prompt modifier"""
        style_modifiers = {
            'realistic': 'A photorealistic image with natural lighting and detailed textures showing',
            'artistic': 'An artistic interpretation with expressive brushstrokes and vibrant colors depicting',
            'fantasy': 'A magical and ethereal fantasy scene with mystical elements portraying'
        }
        modifier = style_modifiers.get(style, style_modifiers['realistic'])
        return f"{modifier}: {text}"

    def _make_api_call(self, prompt: str, width: int = 1024, height: int = 576, max_retries: int = 3) -> Dict:
        """Make API call to generate image with retry logic and rate limiting.
        
        Args:
            prompt: The text prompt for image generation
            width: Image width in pixels
            height: Image height in pixels
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dict containing url, prompt, retries, error (if any), and status
        """
        try:
            # Check rate limit
            current_time = datetime.now()
            while self.image_generation_queue and current_time - self.image_generation_queue[0] > timedelta(seconds=self.IMAGE_RATE_LIMIT):
                self.image_generation_queue.popleft()
            
            if len(self.image_generation_queue) >= 6:
                wait_time = (self.image_generation_queue[0] + timedelta(seconds=self.IMAGE_RATE_LIMIT) - current_time).total_seconds()
                time.sleep(wait_time)

            retry_count = 0
            current_delay = 1
            last_error = None

            while retry_count < max_retries:
                try:
                    image_response = self.client.images.generate(
                        prompt=prompt,
                        model="black-forest-labs/FLUX.1-schnell-Free",
                        width=width,
                        height=height,
                        steps=4,
                        n=1,
                        response_format="b64_json"
                    )
                    
                    if image_response and hasattr(image_response, 'data') and image_response.data:
                        image_b64 = image_response.data[0].b64_json
                        self.image_generation_queue.append(datetime.now())
                        
                        return {
                            'url': f"data:image/png;base64,{image_b64}",
                            'prompt': prompt,
                            'retries': retry_count,
                            'status': 'success'
                        }
                    raise Exception("Invalid response format from image generation API")
                    
                except Exception as e:
                    last_error = e
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.warning(f"Image generation attempt {retry_count} failed: {str(e)}. Retrying in {current_delay} seconds...")
                        time.sleep(current_delay)
                        current_delay *= 2
            
            raise last_error
            
        except Exception as e:
            logger.error(f"Error in API call: {str(e)}")
            return {
                'error': str(e),
                'retries': retry_count,
                'status': 'failed',
                'prompt': prompt
            }

    def generate_image(self, text: str, style: str = 'realistic') -> Dict:
        """Generate a single image from text prompt.
        
        Args:
            text: The base text prompt
            style: Style modifier for the prompt
            
        Returns:
            Dict containing generation result with url/error and metadata
        """
        enhanced_prompt = self._style_to_prompt_modifier(text, style)
        return self._make_api_call(enhanced_prompt)

    def generate_image_chain(self, prompts: List[str], style: str = 'realistic') -> Optional[Dict]:
        """Generate image through multiple refinement steps.
        
        Args:
            prompts: List of text prompts to process sequentially
            style: Style modifier for all prompts
            
        Returns:
            Dict containing final successful generation or None if all attempts fail
        """
        try:
            final_result = None
            
            for i, prompt in enumerate(prompts):
                enhanced_prompt = self._style_to_prompt_modifier(prompt, style)
                step_result = self._make_api_call(enhanced_prompt)
                
                if step_result['status'] == 'success':
                    final_result = step_result
                    if i < len(prompts) - 1:
                        time.sleep(2)
                else:
                    logger.error(f"Chain step {i} failed: {step_result.get('error')}")
                    return step_result

            if final_result and final_result['status'] == 'success':
                return {
                    'url': final_result['url'],
                    'prompt': final_result['prompt'],
                    'steps_completed': str(len(prompts))
                }
            return None
            
        except Exception as e:
            logger.error(f"Error in generate_image_chain: {str(e)}")
            return None
