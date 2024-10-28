import websockets
import json
import asyncio
import base64
import os
import time
from datetime import datetime
import logging
from .supabase_storage import SupabaseStorage

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
        self.storage = SupabaseStorage()

    async def _connect(self):
        self.ws = await websockets.connect(self.ws_url)
        metadata = await self.ws.recv()
        return json.loads(metadata)

    async def _generate_audio_async(self, text):
        try:
            # Connect to websocket
            await self._connect()
            
            # Split long text into sentences if needed
            sentences = text.split('. ')
            full_text = '. '.join(sentences)  # Rejoin with periods to maintain proper sentence structure
            
            logger.info(f"Processing text length: {len(full_text)} characters")
            
            # Send narration request with complete text
            message = {
                "type": "user_input",
                "text": full_text,
                "mode": "narrate"
            }
            await self.ws.send(json.dumps(message))
            
            # Handle response and save audio chunks
            timestamp = int(time.time())
            chunk_urls = []
            chunk_counter = 0
            
            while True:
                response = await self.ws.recv()
                response_data = json.loads(response)
                
                if response_data["type"] == "audio_output":
                    audio_bytes = base64.b64decode(response_data["data"])
                    chunk_counter += 1
                    filename = f"paragraph_{timestamp}_chunk_{chunk_counter}.wav"
                    
                    # Upload chunk to Supabase storage
                    chunk_url = self.storage.upload_audio_chunk(audio_bytes, filename)
                    if chunk_url:
                        chunk_urls.append(chunk_url)
                    
                elif response_data["type"] == "assistant_end":
                    break
                
                elif response_data["type"] == "error":
                    logger.error(f"Error from EVI: {response_data.get('message', 'Unknown error')}")
                    break
            
            await self.ws.close()
            
            if chunk_urls:
                # For now, return the URL of the first chunk
                # In a future enhancement, we could return all URLs or combine the chunks
                return chunk_urls[0]
            return None
            
        except Exception as e:
            logger.error(f"Error generating audio with Hume: {str(e)}")
            if hasattr(self, 'ws'):
                await self.ws.close()
            return None

    def generate_audio(self, text):
        try:
            return asyncio.run(self._generate_audio_async(text))
        except Exception as e:
            logger.error(f"Error in generate_audio: {str(e)}")
            return None
