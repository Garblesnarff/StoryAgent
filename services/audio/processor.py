"""
Audio Processing Module
----------------------
Handles the core audio processing functionality, including text chunking,
audio data collection, and processing pipeline management.
"""

import asyncio
import base64
import logging
from typing import Optional, List, Dict, Any, Tuple
from .connection import HumeWebSocketManager
from .storage import AudioStorage
from .utils import RetryManager

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Handles the processing of text into audio using Hume AI's API."""
    
    def __init__(self):
        """Initialize the audio processor."""
        self.chunk_size = 100  # Maximum characters per chunk
        
    def _split_text(self, text: str) -> List[str]:
        """
        Split input text into manageable chunks for processing.
        
        Args:
            text (str): The text to split into chunks
            
        Returns:
            List[str]: List of text chunks
        """
        chunks = []
        sentences = text.split('. ')
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            # If sentence itself is too long, split it further
            if len(sentence) > self.chunk_size:
                words = sentence.split()
                temp_chunk = []
                temp_length = 0
                
                for word in words:
                    if temp_length + len(word) > self.chunk_size and temp_chunk:
                        chunks.append(' '.join(temp_chunk) + '.')
                        temp_chunk = [word]
                        temp_length = len(word)
                    else:
                        temp_chunk.append(word)
                        temp_length += len(word) + 1
                
                if temp_chunk:
                    chunks.append(' '.join(temp_chunk) + '.')
            else:
                if current_length + len(sentence) > self.chunk_size and current_chunk:
                    chunks.append('. '.join(current_chunk) + '.')
                    current_chunk = [sentence]
                    current_length = len(sentence)
                else:
                    current_chunk.append(sentence)
                    current_length += len(sentence)
        
        if current_chunk:
            chunks.append('. '.join(current_chunk))
            
        return chunks
        
    async def _process_chunk(
        self,
        chunk: str,
        connection: HumeWebSocketManager,
        retry_manager: RetryManager
    ) -> Tuple[bool, bytearray]:
        """
        Process a single text chunk into audio data.
        
        Args:
            chunk (str): Text chunk to process
            connection (HumeWebSocketManager): WebSocket connection manager
            retry_manager (RetryManager): Retry logic handler
            
        Returns:
            Tuple[bool, bytearray]: Success status and audio data
        """
        audio_data = bytearray()
        success = False
        
        try:
            message = {
                "type": "user_input",
                "text": chunk
            }
            
            await connection.send_message(message)
            
            async with asyncio.timeout(30):  # 30-second timeout per chunk
                while True:
                    response = await connection.receive_message()
                    
                    if response["type"] == "audio_output":
                        chunk_data = base64.b64decode(response["data"])
                        audio_data.extend(chunk_data)
                        logger.info(f"Received audio chunk: {len(chunk_data)} bytes")
                    
                    elif response["type"] == "assistant_end":
                        logger.info("Successfully processed chunk")
                        success = True
                        break
                    
                    elif response["type"] == "error":
                        raise Exception(response.get('message', 'Unknown error'))
                        
            return success, audio_data
            
        except Exception as e:
            logger.error(f"Error processing chunk: {str(e)}")
            return False, audio_data

    async def process_text_to_audio(
        self,
        text: str,
        connection: HumeWebSocketManager,
        storage: AudioStorage,
        retry_manager: RetryManager
    ) -> Optional[str]:
        """
        Process text to audio through the complete pipeline.
        
        Args:
            text (str): Text to convert to audio
            connection (HumeWebSocketManager): WebSocket connection handler
            storage (AudioStorage): Audio file storage manager
            retry_manager (RetryManager): Retry logic handler
            
        Returns:
            Optional[str]: URL of the generated audio file, or None if generation failed
        """
        try:
            chunks = self._split_text(text)
            final_audio_data = bytearray()
            
            for chunk_index, chunk in enumerate(chunks):
                retry_count = 0
                success = False
                
                while not success and retry_count < retry_manager.max_retries:
                    try:
                        # Establish new connection for each chunk
                        await connection.connect()
                        
                        success, chunk_audio = await self._process_chunk(
                            chunk,
                            connection,
                            retry_manager
                        )
                        
                        if success:
                            final_audio_data.extend(chunk_audio)
                            logger.info(f"Successfully processed chunk {chunk_index + 1}/{len(chunks)}")
                        else:
                            retry_count += 1
                            await retry_manager.handle_retry(retry_count)
                            
                    except Exception as e:
                        logger.error(f"Error processing chunk {chunk_index + 1}: {str(e)}")
                        retry_count += 1
                        await retry_manager.handle_retry(retry_count)
                    finally:
                        await connection.close()
                
                if not success:
                    logger.error(f"Failed to process chunk {chunk_index + 1} after {retry_manager.max_retries} attempts")
                    return None
            
            if final_audio_data:
                return await storage.save_audio_file(final_audio_data)
                
            return None
            
        except Exception as e:
            logger.error(f"Error in process_text_to_audio: {str(e)}")
            return None
