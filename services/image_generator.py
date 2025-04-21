import os
import logging
import base64
from io import BytesIO
from typing import Dict, List, Optional

from google import genai # Corrected import based on documentation
from google.genai import types # This import seems correct as per docs too
from PIL import Image # Requires Pillow dependency

logger = logging.getLogger(__name__)

class ImageGenerator:
    """
    Generates images using the Google Gemini API.

    Requires the API key to be passed during initialization.
    """
    def __init__(self, api_key: str):
        """Initializes the Gemini client with the provided API key."""
        logger.info(f"ImageGenerator received API key: {'*****' if api_key else 'None'}") # Log received key presence
        try:
            if not api_key:
                # Log the error and raise it if no API key is provided
                error_msg = "API key was not provided to ImageGenerator __init__." # Added context to error
                logger.error(error_msg)
                raise ValueError(error_msg)

            # DO NOT explicitly configure here - relies on env var being set before Client() is called
            # genai.configure(api_key=api_key) # REMOVED - Incorrect based on docs and error

            # Initialize the client exactly as per the documentation
            # This should implicitly pick up the API key from the environment
            self.client = genai.Client()
            logger.info("Gemini Client configured and initialized successfully.")
        except ValueError as ve: # Catch the specific error for missing API key
            logger.error(f"Configuration error: {ve}")
            self.client = None
        except AttributeError as ae:
             # Catching the specific error seen before if import/version is still wrong
             logger.error(f"Failed to initialize Gemini Client due to AttributeError: {ae}. Check 'google-generativeai' library installation and version/imports.")
             self.client = None
        except Exception as e:
            logger.error(f"An unexpected error occurred during Gemini Client initialization: {e}")
            self.client = None

    def _call_gemini_api(self, prompt: str) -> Dict:
        """
        Makes an API call to Gemini to generate an image.

        Args:
            prompt: The text prompt for image generation.

        Returns:
            A dictionary containing the generation result:
            - 'url': Base64 data URI of the generated image if successful.
            - 'prompt': The prompt used.
            - 'status': 'success' or 'failed'.
            - 'error': Error message if status is 'failed'.
        """
        if not self.client: # Check if client initialization failed
            return {
                'error': "Gemini client was not initialized successfully. Check logs.",
                'status': 'failed',
                'prompt': prompt
            }

        try:
            logger.info(f"Generating image with Gemini for prompt: '{prompt[:50]}...'")
            # Using client.models.generate_content exactly as per documentation
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp-image-generation",
                contents=prompt,
                config=types.GenerateContentConfig( # Renamed parameter 'config' as per docs
                    response_modalities=['TEXT', 'IMAGE']
                )
                # Note: No direct width/height control in the documented example
                # for gemini-2.0-flash-exp-image-generation
            )

            image_data = None
            # Iterate through response parts to find the image data
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith('image/'):
                    image_data = part.inline_data.data
                    break # Found the image data

            if image_data:
                # Encode the raw bytes image data to base64
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                logger.info("Successfully generated image.")
                return {
                    'url': f"data:image/png;base64,{image_b64}", # Assuming PNG, adjust if needed
                    'prompt': prompt,
                    'status': 'success'
                }
            else:
                # Check if there was text output instead or just no image
                text_output = ""
                for part in response.candidates[0].content.parts:
                    if part.text:
                        text_output += part.text
                error_message = f"No image data found in Gemini response. Text response: '{text_output}'" if text_output else "No image data found in Gemini response."
                logger.warning(error_message)
                raise ValueError(error_message)

        except Exception as e:
            logger.error(f"Error during Gemini API call: {str(e)}")
            return {
                'error': str(e),
                'status': 'failed',
                'prompt': prompt
            }

    def generate_image(self, text: str) -> Dict:
        """
        Generates a single image from a text prompt using Gemini.

        Args:
            text: The base text prompt.

        Returns:
            Dict containing generation result with url/error and metadata.
        """
        # Style parameter is removed as Gemini handles style interpretation via prompt.
        return self._call_gemini_api(text)

    def generate_image_chain(self, prompts: List[str]) -> Optional[Dict]:
        """
        Generates an image using the *last* prompt in a sequence with Gemini.

        Note: This simplification ignores the intermediate prompts. True chaining
        might require conversational turns with Gemini if context needs building.

        Args:
            prompts: List of text prompts. Only the last one is used.

        Returns:
            Dict containing final generation result or None/error dict if it fails.
        """
        if not prompts:
            logger.warning("generate_image_chain called with empty prompts list.")
            return {'error': 'Empty prompt list provided', 'status': 'failed', 'prompt': ''}

        final_prompt = prompts[-1]
        logger.info(f"Using final prompt from chain: '{final_prompt[:50]}...'")
        # Style parameter is removed.
        result = self._call_gemini_api(final_prompt)

        # Adapt the return format slightly if needed, but _call_gemini_api
        # already returns the desired structure.
        # Add 'steps_completed' for compatibility if necessary, though it's always 1 now.
        if result and result['status'] == 'success':
             result['steps_completed'] = '1' # Indicate only one step (last prompt) was used
             return result
        elif result: # Handles the failure case from _call_gemini_api
            return result
        else: # Should not happen if _call_gemini_api always returns a dict
             return {'error': 'Unknown error in generate_image_chain', 'status': 'failed', 'prompt': final_prompt}
