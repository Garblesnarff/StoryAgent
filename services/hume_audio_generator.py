"""
Hume Audio Generator Service

This module provides audio generation capabilities using Hume AI's websocket-based
text-to-speech API. It handles:
- Chunked text-to-speech conversion
- WebSocket connection management
- Audio data concatenation
- Rate limiting and retries
- Error handling and logging

The service automatically splits long text into manageable chunks and handles
reconnection logic for reliable audio generation.
"""

import websockets
import json
import asyncio
import base64
import os
import time
from datetime import datetime
import logging
import wave
from typing import Optional, Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HumeAudioGenerator:
    """
    Audio generation service using Hume AI's websocket API.
    
    This class manages websocket connections to Hume's API and handles
    text-to-speech generation with automatic chunking and retry logic.
    
    Attributes:
        audio_dir: Directory for storing generated audio files
        ws_url: WebSocket URL for Hume API connection
    """
    
    def __init__(self):
        """
        Initialize the audio generator with required configurations.
        
        Sets up:
        - Audio storage directory
        - WebSocket connection parameters
        - API authentication
        
        Raises:
            EnvironmentError: If required API credentials are not set
        """
        self.audio_dir = os.path.join('static', 'audio')
        os.makedirs(self.audio_dir, exist_ok=True)

        # Initialize connection parameters
        base_url = "wss://api.hume.ai/v0/evi/chat"
        config_id = os.environ.get('HUME_CONFIG_ID')
        api_key = os.environ.get('HUME_API_KEY')
        
        if not config_id or not api_key:
            raise EnvironmentError("Missing required Hume API credentials")

        params = [
            f"config_id={config_id}",
            "evi_version=2",
            f"api_key={api_key}"
        ]

        self.ws_url = f"{base_url}?{'&'.join(params)}"

    async def _connect(self) -> Dict:
        """
        Establish WebSocket connection to Hume API.
        
        Returns:
            Dict: Connection metadata from the server
            
        Raises:
            websockets.exceptions.WebSocketException: If connection fails
        """
        self.ws = await websockets.connect(self.ws_url)
        metadata = await self.ws.recv()
        return json.loads(metadata)

    async def _generate_audio_async(self, text: str) -> Optional[str]:
        """
        Generate audio asynchronously with chunking and retry logic.
        
        Args:
            text: Input text to convert to speech
            
        Returns:
            Optional[str]: URL path to the generated audio file, or None if generation fails
            
        Raises:
            Exception: If audio generation fails after all retries
        """
        try:
            # Initialize audio data collection
            audio_data = bytearray()
            
            # Split text into smaller chunks (around 100 characters each)
            chunks = []
            max_chunk_size = 100
            sentences = text.split('. ')
            current_chunk = []
            current_length = 0
            
            for sentence in sentences:
                # If sentence itself is too long, split it further
                if len(sentence) > max_chunk_size:
                    words = sentence.split()
                    temp_chunk = []
                    temp_length = 0
                    
                    for word in words:
                        if temp_length + len(word) > max_chunk_size and temp_chunk:
                            chunks.append(' '.join(temp_chunk) + '.')
                            temp_chunk = [word]
                            temp_length = len(word)
                        else:
                            temp_chunk.append(word)
                            temp_length += len(word) + 1
                    
                    if temp_chunk:
                        chunks.append(' '.join(temp_chunk) + '.')
                else:
                    if current_length + len(sentence) > max_chunk_size and current_chunk:
                        chunks.append('. '.join(current_chunk) + '.')
                        current_chunk = [sentence]
                        current_length = len(sentence)
                    else:
                        current_chunk.append(sentence)
                        current_length += len(sentence)
            
            if current_chunk:
                chunks.append('. '.join(current_chunk))
            
            # Process each chunk with retries
            for chunk in chunks:
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        # Connect for each chunk to ensure fresh connection
                        await self._connect()
                        
                        logger.info(f"Processing text chunk: {len(chunk)} characters")
                        message = {
                            "type": "user_input",
                            "text": chunk
                        }
                        
                        await self.ws.send(json.dumps(message))
                        
                        # Collect audio data for this chunk
                        while True:
                            response = await self.ws.recv()
                            response_data = json.loads(response)
                            
                            if response_data["type"] == "audio_output":
                                chunk_data = base64.b64decode(response_data["data"])
                                audio_data.extend(chunk_data)
                                logger.info(f"Received audio chunk: {len(chunk_data)} bytes")
                            
                            elif response_data["type"] == "assistant_end":
                                logger.info("Received end of chunk signal")
                                break
                            
                            elif response_data["type"] == "error":
                                raise Exception(response_data.get('message', 'Unknown error'))
                        
                        # Add small delay between chunks
                        await asyncio.sleep(0.5)
                        break  # Success, exit retry loop
                        
                    except Exception as e:
                        logger.error(f"Error processing chunk (attempt {retry_count + 1}): {str(e)}")
                        retry_count += 1
                        if retry_count == max_retries:
                            logger.error(f"Failed to process chunk after {max_retries} attempts")
                            return None
                        await asyncio.sleep(1)  # Wait before retry
                    finally:
                        if hasattr(self, 'ws'):
                            await self.ws.close()
                            logger.info("WebSocket connection closed")

            # Save complete audio file
            if audio_data:
                filename = f"paragraph_audio_{int(time.time())}.wav"
                filepath = os.path.join(self.audio_dir, filename)
                
                with wave.open(filepath, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(24000)
                    wav_file.writeframes(audio_data)
                
                logger.info(f"Saved audio file: {filename} ({len(audio_data)} bytes)")
                return f"/static/audio/{filename}"
            
            logger.warning("No audio data received")
            return None
            
        except Exception as e:
            logger.error(f"Error generating audio with Hume: {str(e)}")
            return None

    def generate_audio(self, text: str) -> Optional[str]:
        """
        Generate audio from text using Hume's text-to-speech service.
        
        This is the main entry point for audio generation. It handles the async
        execution and provides a synchronous interface for the rest of the application.
        
        Args:
            text: The text to convert to speech
            
        Returns:
            Optional[str]: URL path to the generated audio file, or None if generation fails
        """
        try:
            return asyncio.run(self._generate_audio_async(text))
        except Exception as e:
            logger.error(f"Error in generate_audio: {str(e)}")
            return None
