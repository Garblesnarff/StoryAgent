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
        base_text = text[:200]  # Get first 200 chars of text for context
        
        if style == 'realistic':
            return (
                f"Photorealistic digital photograph of {base_text}. Shot on Canon EOS R5, "
                f"natural daylight, 4K resolution, extreme detail, photojournalistic style. "
                f"Hyperrealistic textures, accurate lighting and shadows, perfect focus, "
                f"high dynamic range. Style of National Geographic photography."
            )
        elif style == 'artistic':
            return (
                f"Oil painting interpretation of: {base_text}. In the distinctive style of "
                f"Van Gogh and Monet, with visible brushstrokes, vibrant impasto technique, "
                f"bold colors and expressive artistic interpretation. Painted on canvas with "
                f"thick oil paints, showing texture and movement. Impressionistic lighting "
                f"and dreamlike atmosphere."
            )
        elif style == 'fantasy':
            return (
                f"High fantasy digital artwork of: {base_text}. In the style of legendary "
                f"fantasy artists like Michael Whelan and Frank Frazetta. Magical atmosphere "
                f"with glowing ethereal lights, mystical fog effects, iridescent colors. "
                f"Dragons, floating crystals, and magical energy in the environment. "
                f"Dramatic fantasy lighting with lens flares and god rays."
            )
        else:
            return f"An image representing: {base_text}"
        
    def generate_image(self, text, style='realistic'):
        try:
            # Check rate limit
            current_time = datetime.now()
            while self.image_generation_queue and current_time - self.image_generation_queue[0] > timedelta(seconds=self.IMAGE_RATE_LIMIT):
                self.image_generation_queue.popleft()
            
            if len(self.image_generation_queue) >= 6:
                wait_time = (self.image_generation_queue[0] + timedelta(seconds=self.IMAGE_RATE_LIMIT) - current_time).total_seconds()
                time.sleep(wait_time)
            
            # Generate enhanced prompt with style
            enhanced_prompt = self._style_to_prompt_modifier(text, style)
            
            # Generate image using Together AI
            image_response = self.client.images.generate(
                prompt=enhanced_prompt,
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
                
                return f"data:image/png;base64,{image_b64}"
            return None
            
        except Exception as e:
            print(f"Error generating image: {str(e)}")
            return None
