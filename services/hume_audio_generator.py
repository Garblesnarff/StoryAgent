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

    async def _generate_audio_async(self, text):
        try:
            # Connect to websocket
            await self._connect()
            
            # Initialize audio data collection
            audio_data = bytearray()
            
            # Split text into smaller chunks (around 200 characters each)
            # Trying to split at sentence boundaries when possible
            chunks = []
            max_chunk_size = 200
            sentences = text.split('. ')
            current_chunk = []
            current_length = 0
            
            for sentence in sentences:
                if current_length + len(sentence) > max_chunk_size and current_chunk:
                    chunks.append('. '.join(current_chunk) + '.')
                    current_chunk = [sentence]
                    current_length = len(sentence)
                else:
                    current_chunk.append(sentence)
                    current_length += len(sentence)
                    
            if current_chunk:
                chunks.append('. '.join(current_chunk))
            
            # Process each chunk
            for chunk in chunks:
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
                        logger.error(f"Error from EVI: {response_data.get('message', 'Unknown error')}")
                        return None

            # Save complete audio file
            if audio_data:
                filename = f"paragraph_audio_{int(time.time())}.wav"
                filepath = os.path.join(self.audio_dir, filename)
                
                with wave.open(filepath, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(24000)  # 24kHz sample rate
                    wav_file.writeframes(audio_data)
                
                logger.info(f"Saved audio file: {filename} ({len(audio_data)} bytes)")
                return f"/static/audio/{filename}"
                
            logger.warning("No audio data received")
            return None
            
        except Exception as e:
            logger.error(f"Error generating audio with Hume: {str(e)}")
            return None
        finally:
            if hasattr(self, 'ws'):
                await self.ws.close()
                logger.info("WebSocket connection closed")

    def generate_audio(self, text):
        try:
            return asyncio.run(self._generate_audio_async(text))
        except Exception as e:
            logger.error(f"Error in generate_audio: {str(e)}")
            return None
