import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RegenerationService:
    def __init__(self, image_service, audio_service):
        self.image_service = image_service
        self.audio_service = audio_service
        logger.info("Regeneration Service: Initialized with image and audio services")

    def regenerate_image(self, text: str) -> str:
        """Regenerate an image for the given text"""
        try:
            logger.info("Regeneration Service: Starting image regeneration...")
            image_url = self.image_service.generate_image(text)
            
            if not image_url:
                logger.error("Regeneration Service: Failed to regenerate image")
                raise Exception("Failed to regenerate image")
                
            logger.info("Regeneration Service: Successfully regenerated image")
            return image_url

        except Exception as e:
            logger.error(f"Regeneration Service Error: {str(e)}")
            return None

    def regenerate_audio(self, text: str) -> str:
        """Regenerate audio for the given text"""
        try:
            logger.info("Regeneration Service: Starting audio regeneration...")
            audio_url = self.audio_service.generate_audio(text)
            
            if not audio_url:
                logger.error("Regeneration Service: Failed to regenerate audio")
                raise Exception("Failed to regenerate audio")
                
            logger.info("Regeneration Service: Successfully regenerated audio")
            return audio_url

        except Exception as e:
            logger.error(f"Regeneration Service Error: {str(e)}")
            return None
