"""
Audio Storage Module
------------------
Handles the storage and management of generated audio files, including
file naming, saving, and URL generation.
"""

import os
import time
import wave
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AudioStorage:
    """Manages the storage of generated audio files."""
    
    def __init__(self):
        """Initialize the audio storage manager."""
        self.audio_dir = os.path.join('static', 'audio')
        os.makedirs(self.audio_dir, exist_ok=True)
        
    def _generate_filename(self) -> str:
        """
        Generate a unique filename for the audio file.
        
        Returns:
            str: Generated filename
        """
        timestamp = int(time.time())
        return f"generated_audio_{timestamp}.wav"
        
    async def save_audio_file(self, audio_data: bytearray) -> Optional[str]:
        """
        Save audio data to a WAV file.
        
        Args:
            audio_data (bytearray): The audio data to save
            
        Returns:
            Optional[str]: URL path to the saved audio file, or None if saving failed
        """
        try:
            if not audio_data:
                logger.warning("No audio data to save")
                return None
                
            filename = self._generate_filename()
            filepath = os.path.join(self.audio_dir, filename)
            
            with wave.open(filepath, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono audio
                wav_file.setsampwidth(2)  # 2 bytes per sample
                wav_file.setframerate(24000)  # 24kHz sample rate
                wav_file.writeframes(audio_data)
                
            logger.info(f"Saved audio file: {filename} ({len(audio_data)} bytes)")
            return f"/static/audio/{filename}"
            
        except Exception as e:
            logger.error(f"Error saving audio file: {str(e)}")
            return None
