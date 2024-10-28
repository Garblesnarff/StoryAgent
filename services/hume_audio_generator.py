import websockets
import json
import asyncio
import base64
import os
import time
from datetime import datetime
import logging
from .postgresql_storage import PostgresqlStorage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HumeAudioGenerator:
    def __init__(self, app=None):
        # Initialize connection parameters
        base_url = "wss://api.hume.ai/v0/evi/chat"
        config_id = os.environ.get('HUME_CONFIG_ID')
        api_key = os.environ.get('HUME_API_KEY')
        
        if not all([config_id, api_key]):
            raise ValueError("Missing required Hume AI credentials")
        
        params = [
            f"config_id={config_id}",
            "evi_version=2",
            f"api_key={api_key}"
        ]
        
        self.ws_url = f"{base_url}?{'&'.join(params)}"
        try:
            self.storage = PostgresqlStorage(app)
            logger.info("PostgreSQL storage initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL storage: {str(e)}")
            raise

    async def _connect(self):
        try:
            self.ws = await websockets.connect(self.ws_url)
            metadata = await self.ws.recv()
            metadata_json = json.loads(metadata)
            logger.info(f"Connected to Hume EVI with chat_id: {metadata_json.get('chat_id')}")
            return metadata_json
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            raise

    async def _generate_audio_async(self, text):
        """Generate audio for a complete paragraph"""
        try:
            # Connect to websocket
            await self._connect()
            logger.info("Connected to Hume EVI websocket")
            
            # Send text for narration
            message = {
                "type": "user_input",
                "text": text,
                "mode": "narrate"
            }
            await self.ws.send(json.dumps(message))
            logger.info("Sent text for narration")
            
            # Handle response and save audio
            timestamp = int(time.time())
            filename = f"paragraph_audio_{timestamp}.wav"
            all_audio_bytes = bytearray()
            
            while True:
                try:
                    response = await self.ws.recv()
                    response_data = json.loads(response)
                    
                    if response_data["type"] == "audio_output":
                        audio_bytes = base64.b64decode(response_data["data"])
                        all_audio_bytes.extend(audio_bytes)
                        logger.info("Received audio chunk")
                    
                    elif response_data["type"] == "assistant_end":
                        logger.info("Audio generation complete")
                        break
                    
                    elif response_data["type"] == "error":
                        error_msg = response_data.get('message', 'Unknown error')
                        logger.error(f"Error from EVI: {error_msg}")
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing audio chunk: {str(e)}")
                    break
            
            await self.ws.close()
            
            if all_audio_bytes:
                # Upload complete audio to PostgreSQL
                logger.info(f"Uploading complete audio file ({len(all_audio_bytes)} bytes) to PostgreSQL")
                audio_url = self.storage.upload_audio_chunk(all_audio_bytes, filename)
                if audio_url:
                    logger.info("Audio uploaded successfully")
                    return audio_url
                else:
                    logger.error("Failed to upload audio")
            return None
            
        except Exception as e:
            logger.error(f"Error generating audio with Hume: {str(e)}")
            if hasattr(self, 'ws'):
                await self.ws.close()
            return None

    def generate_audio(self, text):
        """Synchronous wrapper for audio generation"""
        try:
            # Create new event loop for async operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_url = loop.run_until_complete(self._generate_audio_async(text))
            loop.close()
            return audio_url
        except Exception as e:
            logger.error(f"Error in generate_audio: {str(e)}")
            return None
