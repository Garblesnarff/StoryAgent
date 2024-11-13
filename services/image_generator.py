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
            'realistic': 'Photorealistic style, ultra detailed digital art, natural lighting, 4k uhd',
            'artistic': 'Oil painting style, impressionist artwork, vibrant colors, expressive brushstrokes, artistic interpretation',
            'fantasy': 'Fantasy digital art, magical atmosphere, ethereal lighting, mystical elements, dreamlike quality'
        }
        modifier = style_modifiers.get(style, style_modifiers['realistic'])
        # Place the style modifier at the beginning and emphasize it
        return f"{modifier}, create an image representing: {text[:100]}"
        
    def generate_image(self, text, style='realistic'):
        try:
            # Check rate limit
            current_time = datetime.now()
            while self.image_generation_queue and current_time - self.image_generation_queue[0] > timedelta(seconds=self.IMAGE_RATE_LIMIT):
                self.image_generation_queue.popleft()
            
            if len(self.image_generation_queue) >= 6:
                wait_time = (self.image_generation_queue[0] + timedelta(seconds=self.IMAGE_RATE_LIMIT) - current_time).total_seconds()
                time.sleep(wait_time)
            
            # Extract style and text from different input formats
            if isinstance(text, dict):
                style = text.get('style', 'realistic')
                text = text['text']
            
            # Apply style modifier
            modified_prompt = self._style_to_prompt_modifier(text, style)
            
            # Generate image using Together AI
            image_response = self.client.images.generate(
                prompt=modified_prompt,
                model="black-forest-labs/FLUX.1-schnell-Free",
                width=512,
                height=512,
                steps=4,
                n=1,
                response_format="b64_json"
            )
            
            if image_response and hasattr(image_response, 'data') and image_response.data:
                image_b64 = image_response.data[0].b64_json
                
                # Add timestamp to queue
                self.image_generation_queue.append(datetime.now())
                
                return {
                    'image_url': f"data:image/png;base64,{image_b64}",
                    'prompt': modified_prompt,
                    'style': style
                }
            return None
            
        except Exception as e:
            print(f"Error generating image: {str(e)}")
            return None
