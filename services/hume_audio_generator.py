import websockets
import json
import asyncio
import base64
import os
import time
from datetime import datetime
import logging

# Set up logging
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
            await self._connect()
            
            # Split long text into sentences if needed
            sentences = text.split('. ')
            full_text = '. '.join(sentences)
            
            logger.info(f"Processing text length: {len(full_text)} characters")
            
            message = {
                "type": "user_input",
                "text": full_text,
                "mode": "narrate"
            }
            await self.ws.send(json.dumps(message))
            
            # Collect all audio chunks
            audio_chunks = []
            chunk_count = 0
            
            while True:
                response = await self.ws.recv()
                response_data = json.loads(response)
                
                if response_data["type"] == "audio_output":
                    chunk_count += 1
                    audio_bytes = base64.b64decode(response_data["data"])
                    audio_chunks.append(audio_bytes)
                    logger.info(f"Received audio chunk {chunk_count}")
                
                elif response_data["type"] == "assistant_end":
                    break
                
                elif response_data["type"] == "error":
                    logger.error(f"Error from EVI: {response_data.get('message', 'Unknown error')}")
                    break
            
            if audio_chunks:
                # Combine all audio chunks
                filename = f"paragraph_audio_{int(time.time())}.wav"
                filepath = os.path.join(self.audio_dir, filename)
                
                # Write combined audio file
                with open(filepath, 'wb') as f:
                    for chunk in audio_chunks:
                        f.write(chunk)
                
                logger.info(f"Saved combined audio file with {len(audio_chunks)} chunks")
                return f"/static/audio/{filename}"
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating audio with Hume: {str(e)}")
            if hasattr(self, 'ws'):
                await self.ws.close()
            return None
        finally:
            if hasattr(self, 'ws'):
                await self.ws.close()

    def generate_audio(self, text):
        try:
            return asyncio.run(self._generate_audio_async(text))
        except Exception as e:
            logger.error(f"Error in generate_audio: {str(e)}")
            return None
