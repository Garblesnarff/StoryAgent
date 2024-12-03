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

    async def _connect(self):
        self.ws = await websockets.connect(self.ws_url)
        metadata = await self.ws.recv()
        return json.loads(metadata)

    async def _generate_audio_async(self, text, max_connection_retries=3, chunk_retries=3):
        try:
            # Initialize audio data collection
            audio_data = bytearray()
            failed_chunks = []
            
            # Split text into smaller chunks (around 100 characters each)
            chunks = []
            max_chunk_size = 100  # Reduced from 200 to 100
            sentences = text.split('. ')
            current_chunk = []
            current_length = 0
            
            # Track overall progress
            total_chunks = 0
            processed_chunks = 0
            
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
            
            # Process each chunk with enhanced retry logic
            for chunk_index, chunk in enumerate(chunks):
                connection_retry_count = 0
                chunk_retry_count = 0
                success = False
                
                while not success and connection_retry_count < max_connection_retries:
                    try:
                        # Connect for each chunk with retry logic
                        connection_attempts = 0
                        while connection_attempts < 3:
                            try:
                                await self._connect()
                                break
                            except Exception as conn_error:
                                connection_attempts += 1
                                if connection_attempts == 3:
                                    raise Exception(f"Failed to establish connection after 3 attempts: {str(conn_error)}")
                                await asyncio.sleep(1)
                        
                        logger.info(f"Processing text chunk {chunk_index + 1}/{len(chunks)}: {len(chunk)} characters")
                        message = {
                            "type": "user_input",
                            "text": chunk
                        }
                        
                        await self.ws.send(json.dumps(message))
                        chunk_success = False
                        chunk_data_buffer = bytearray()
                        
                        # Collect audio data for this chunk with timeout
                        try:
                            async with asyncio.timeout(30):  # 30-second timeout per chunk
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
                                        raise Exception(response_data.get('message', 'Unknown error'))
                                    
                            if chunk_success:
                                audio_data.extend(chunk_data_buffer)
                                processed_chunks += 1
                                success = True
                                # Add small delay between chunks
                                await asyncio.sleep(0.5)
                                break  # Success, exit retry loop
                                
                        except asyncio.TimeoutError:
                            logger.error(f"Timeout processing chunk {chunk_index + 1}")
                            raise Exception("Chunk processing timeout")
                        
                    except Exception as e:
                        error_msg = f"Error processing chunk {chunk_index + 1} (attempt {chunk_retry_count + 1}): {str(e)}"
                        logger.error(error_msg)
                        chunk_retry_count += 1
                        connection_retry_count += 1
                        
                        if chunk_retry_count == chunk_retries:
                            logger.error(f"Failed to process chunk {chunk_index + 1} after {chunk_retries} attempts")
                            failed_chunks.append({
                                'index': chunk_index,
                                'text': chunk,
                                'error': str(e)
                            })
                            break
                            
                        await asyncio.sleep(2 ** chunk_retry_count)  # Exponential backoff
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

    def generate_audio(self, text):
        try:
            return asyncio.run(self._generate_audio_async(text))
        except Exception as e:
            logger.error(f"Error in generate_audio: {str(e)}")
            return None
