import os
import json
import logging
from PIL import Image
import requests
from io import BytesIO

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageGenerator:
    def __init__(self):
        # Initialize API configuration
        self.api_key = os.environ.get('TOGETHER_API_KEY')
        self.api_url = "https://api.together.xyz/inference"
        self.image_dir = os.path.join('static', 'images')
        os.makedirs(self.image_dir, exist_ok=True)

    def generate_image(self, text: str) -> str:
        """Generate an image based on the text description"""
        try:
            logger.info("Image Generator: Starting image generation...")
            logger.info(f"Image Generator: Generating image for text of length {len(text)}")

            # Prepare the API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Create a more detailed prompt for better image generation
            enhanced_prompt = (
                f"Create a vivid, detailed illustration for this story excerpt: {text}\n"
                "Style: Digital art, high quality, detailed, cohesive composition"
            )

            payload = {
                "model": "stabilityai/stable-diffusion-2-1",
                "prompt": enhanced_prompt,
                "negative_prompt": "text, watermark, signature, blurry, distorted",
                "num_inference_steps": 30,
                "width": 768,
                "height": 512
            }

            logger.info("Image Generator: Sending request to API...")
            response = requests.post(self.api_url, headers=headers, json=payload)

            if response.status_code != 200:
                logger.error(f"Image Generator Error: API request failed with status {response.status_code}")
                logger.error(f"Image Generator Error: {response.text}")
                raise Exception(f"API request failed with status {response.status_code}")

            # Process the image data
            image_data = response.json()
            if not image_data or 'output' not in image_data:
                logger.error("Image Generator Error: Invalid response format from API")
                raise Exception("Invalid response format from API")

            # Save the image
            image_bytes = BytesIO(image_data['output'].encode('utf-8'))
            image = Image.open(image_bytes)
            
            filename = f"story_image_{int(time.time())}.png"
            filepath = os.path.join(self.image_dir, filename)
            
            image.save(filepath, format='PNG')
            logger.info(f"Image Generator: Successfully saved image as {filename}")
            
            return f"/static/images/{filename}"

        except Exception as e:
            logger.error(f"Image Generator Error: {str(e)}")
            return None
