
import websockets
import json
import asyncio
import base64
import os
import time
from datetime import datetime
import logging
import wave

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HumeAudioGenerator:
    def __init__(self):
        self.audio_dir = os.path.join('static', 'audio')
        os.makedirs(self.audio_dir, exist_ok=True)

        # Initialize connection parameters
        base_url = "wss://api.hume.ai/v0/evi/chat"
        config_id = os.environ.get('HUME_CONFIG_ID')
        api_key = os.environ.get('HUME_API_KEY')

        params = [
            f"config_id={config_id}",
            "evi_version=2",
            f"api_key={api_key}"
        ]

        self.ws_url = f"{base_url}?{'&'.join(params)}"
        self.ws = None

    async def _connect(self):
        """
        Establishes a WebSocket connection to the Hume API.
        
        Returns:
            websockets.WebSocketClientProtocol: The established WebSocket connection
            
        Raises:
            websockets.exceptions.WebSocketException: If connection fails
        """
        try:
            ws = await websockets.connect(self.ws_url)
            metadata = await ws.recv()
            logger.info("Successfully established WebSocket connection")
            return ws
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection: {str(e)}")
            raise

    async def _generate_audio_async(self, text, max_connection_retries=3, chunk_retries=3):
        """
        Asynchronously generates audio from text using Hume API with improved error handling.
        
        Args:
            text (str): Input text to convert to audio
            max_connection_retries (int): Maximum connection retry attempts
            chunk_retries (int): Maximum chunk processing retry attempts
            
        Returns:
            str: Path to generated audio file or None if generation fails
        """
        audio_data = bytearray()
        failed_chunks = []
        
        # Prepare text chunks
        chunks = []
        max_chunk_size = 100
        sentences = text.split('. ')
        current_chunk = []
        current_length = 0
        
        # Text chunking logic
        for sentence in sentences:
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

        # Process chunks
        try:
            self.ws = await self._connect()
            
            for chunk_index, chunk in enumerate(chunks):
                chunk_retry_count = 0
                success = False
                
                while not success and chunk_retry_count < chunk_retries:
                    try:
                        message = {
                            "type": "user_input",
                            "text": chunk
                        }
                        
                        await self.ws.send(json.dumps(message))
                        chunk_success = False
                        chunk_data_buffer = bytearray()
                        
                        async with asyncio.timeout(30):
                            while True:
                                response = await self.ws.recv()
                                response_data = json.loads(response)
                                
                                if response_data["type"] == "audio_output":
                                    chunk_data = base64.b64decode(response_data["data"])
                                    chunk_data_buffer.extend(chunk_data)
                                    logger.info(f"Received audio chunk: {len(chunk_data)} bytes")
                                
                                elif response_data["type"] == "assistant_end":
                                    logger.info(f"Successfully processed chunk {chunk_index + 1}/{len(chunks)}")
                                    chunk_success = True
                                    break
                                
                                elif response_data["type"] == "error":
                                    raise Exception(response_data.get('message', 'Unknown error from Hume API'))
                        
                        if chunk_success:
                            audio_data.extend(chunk_data_buffer)
                            success = True
                            await asyncio.sleep(0.5)
                            break
                            
                    except asyncio.TimeoutError:
                        logger.error(f"Timeout processing chunk {chunk_index + 1}")
                        chunk_retry_count += 1
                        await asyncio.sleep(2 ** chunk_retry_count)
                    except Exception as e:
                        logger.error(f"Error processing chunk {chunk_index + 1} (attempt {chunk_retry_count + 1}): {str(e)}")
                        chunk_retry_count += 1
                        await asyncio.sleep(2 ** chunk_retry_count)
                
                if not success:
                    failed_chunks.append({
                        'index': chunk_index,
                        'text': chunk,
                        'error': 'Maximum retry attempts reached'
                    })

            # Save audio file if we have data
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
            logger.error(f"Error in audio generation: {str(e)}")
            return None
        finally:
            if self.ws:
                try:
                    await self.ws.close()
                    logger.info("WebSocket connection closed")
                except Exception as e:
                    logger.error(f"Error closing WebSocket connection: {str(e)}")

    def generate_audio(self, text):
        """
        Synchronous wrapper for audio generation.
        
        Args:
            text (str): Input text to convert to audio
            
        Returns:
            str: Path to generated audio file or None if generation fails
        """
        try:
            return asyncio.run(self._generate_audio_async(text))
        except Exception as e:
            logger.error(f"Error in generate_audio: {str(e)}")
            return None
