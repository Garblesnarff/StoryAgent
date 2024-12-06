"""
Hume Audio Generation Service
----------------------------
This module provides the main interface for generating audio content using Hume AI's API.
It coordinates between different components for WebSocket communication, audio processing,
and file storage.

Example usage:
    generator = HumeAudioGenerator()
    audio_url = generator.generate_audio("Text to convert to speech")
"""

import logging
from typing import Optional
from .connection import HumeWebSocketManager
from .processor import AudioProcessor
from .storage import AudioStorage
from .utils import RetryManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HumeAudioGenerator:
    """Main class for handling audio generation through Hume AI's API."""
    
    def __init__(self):
        """Initialize the audio generator with its component managers."""
        self.connection_manager = HumeWebSocketManager()
        self.audio_processor = AudioProcessor()
        self.storage = AudioStorage()
        self.retry_manager = RetryManager()
        
    def generate_audio(self, text: str) -> Optional[str]:
        """
        Generate audio from the given text using Hume AI's API.
        
        Args:
            text (str): The text to convert to speech
            
        Returns:
            Optional[str]: URL of the generated audio file, or None if generation failed
            
        Note:
            This method handles the complete pipeline of:
            1. Establishing WebSocket connection
            2. Sending text for processing
            3. Collecting and processing audio data
            4. Saving the audio file
            5. Managing retries on failures
        """
        try:
            return self.audio_processor.process_text_to_audio(
                text,
                self.connection_manager,
                self.storage,
                self.retry_manager
            )
        except Exception as e:
            logger.error(f"Error in generate_audio: {str(e)}")
            return None
