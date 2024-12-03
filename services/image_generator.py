from typing import Dict, List, Optional
import time
import os
import logging

logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from collections import deque
from together import Together
import os
import time

class ImageGenerator:
    def __init__(self):
        # Initialize Together AI client
        self.client = Together(api_key=os.environ.get('TOGETHER_AI_API_KEY'))
        
        # Rate limiting settings
        self.image_generation_queue = deque(maxlen=6)
        self.IMAGE_RATE_LIMIT = 60  # 60 seconds (1 minute)

    def _style_to_prompt_modifier(self, text, style='realistic'):
        """Convert style parameter to prompt modifier"""
        style_modifiers = {
            'realistic': 'A photorealistic image with natural lighting and detailed textures showing',
            'artistic': 'An artistic interpretation with expressive brushstrokes and vibrant colors depicting',
            'fantasy': 'A magical and ethereal fantasy scene with mystical elements portraying'
        }
        modifier = style_modifiers.get(style, style_modifiers['realistic'])
        return f"{modifier}: {text}"
        
    def generate_image(self, text, style='realistic', max_retries=3, initial_delay=1):
        try:
            # Check rate limit
            current_time = datetime.now()
            while self.image_generation_queue and current_time - self.image_generation_queue[0] > timedelta(seconds=self.IMAGE_RATE_LIMIT):
                self.image_generation_queue.popleft()
            
            if len(self.image_generation_queue) >= 6:
                wait_time = (self.image_generation_queue[0] + timedelta(seconds=self.IMAGE_RATE_LIMIT) - current_time).total_seconds()
                time.sleep(wait_time)
            
            # Create enhanced prompt with style
            enhanced_prompt = self._style_to_prompt_modifier(text, style)
            
            # Initialize retry variables
            retry_count = 0
            current_delay = initial_delay
            last_error = None

            while retry_count < max_retries:
                try:
                    # Generate image using Together AI with 16:9 aspect ratio
                    image_response = self.client.images.generate(
                        prompt=enhanced_prompt,
                        model="black-forest-labs/FLUX.1-schnell-Free",
                        width=1024,  # 16:9 ratio
                        height=576,
                        steps=4,
                        n=1,
                        response_format="b64_json"
                    )
                    
                    if image_response and hasattr(image_response, 'data') and image_response.data:
                        image_b64 = image_response.data[0].b64_json
                        
                        # Add timestamp to queue
                        self.image_generation_queue.append(datetime.now())
                        
                        return {
                            'url': f"data:image/png;base64,{image_b64}",
                            'prompt': enhanced_prompt,
                            'retries': retry_count
                        }
                    raise Exception("Invalid response format from image generation API")
                    
                except Exception as e:
                    last_error = e
                    retry_count += 1
                    
                    if retry_count < max_retries:
                        logger.warning(f"Image generation attempt {retry_count} failed: {str(e)}. Retrying in {current_delay} seconds...")
                        time.sleep(current_delay)
                        current_delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"All image generation attempts failed after {max_retries} retries. Last error: {str(e)}")
            
            # If we get here, all retries failed
            raise last_error
            
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return {
                'error': str(e),
                'retries': retry_count,
                'status': 'failed'
            }


    def generate_image_chain(self, prompts: List[str], style: str = 'realistic') -> Optional[Dict[str, str]]:
        """Generate image through multiple refinement steps"""
        try:
            final_image = None
            final_prompt = None
            
            for i, prompt in enumerate(prompts):
                # Generate image for current step
                step_result = self.generate_image(prompt, style)
                
                if isinstance(step_result, dict):
                    final_image = str(step_result.get('url', ''))
                    final_prompt = str(step_result.get('prompt', ''))
                    
                    # If this isn't the final step, allow some time for the model to process
                    if i < len(prompts) - 1:
                        time.sleep(2)  # Brief pause between steps
                
            if final_image and final_prompt:
                return {
                    'url': final_image,
                    'prompt': final_prompt,
                    'steps_completed': str(len(prompts))
                }
            return None
            
        except Exception as e:
            logger.error(f"Error in generate_image_chain: {str(e)}")
            return None