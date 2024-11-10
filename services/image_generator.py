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
        """Convert style parameter to enhanced prompt with specific style elements"""
        base_text = text[:200]  # Get first 200 chars of text for context
        
        if style == 'realistic':
            return (
                f"A scene showing {base_text}, captured with a professional DSLR camera. "
                f"The scene features detailed elements with natural lighting and ambient atmosphere. "
                f"The image has a photorealistic feel, emphasizing textures and materials. "
                f"Include details like surface reflections and environmental details to enhance realism."
            )
        elif style == 'artistic':
            return (
                f"Create an impressionistic interpretation of: {base_text}. "
                f"Use a color palette dominated by rich, harmonious colors to convey the scene's emotion. "
                f"The composition should focus on the main elements, with expressive brushstrokes "
                f"and artistic lighting to add visual interest. Incorporate creative artistic elements "
                f"for a distinctive painted look."
            )
        elif style == 'fantasy':
            return (
                f"Imagine a fantastical interpretation of: {base_text}. "
                f"The scene depicts the action in a magical setting with otherworldly elements. "
                f"Surround the scene with mystical details and ethereal lighting effects. "
                f"Use a color scheme of iridescent colors with glowing accents to create "
                f"a mystical ambiance. Add fantasy elements to enhance the otherworldly feel."
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
