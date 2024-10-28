import websockets
import json
import asyncio
import base64
import os
import time
from datetime import datetime
import logging
import wave
import io

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HumeAudioGenerator:
    def __init__(self):
        self.audio_dir = os.path.join('static', 'audio')
        os.makedirs(self.audio_dir, exist_ok=True)
        logger.info(f"Audio directory initialized: {self.audio_dir}")
        
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
        logger.info("HumeAudioGenerator initialized")

    async def _connect(self):
        logger.info("Connecting to Hume EVI service...")
        self.ws = await websockets.connect(self.ws_url)
        metadata = await self.ws.recv()
        metadata_json = json.loads(metadata)
        logger.info(f"Connected successfully with chat_id: {metadata_json.get('chat_id')}")
        return metadata_json

    async def _generate_audio_async(self, text):
        try:
            logger.info("Connecting to Hume EVI service...")
            await self._connect()
            logger.info("Connected successfully")
            
            sentences = text.split('. ')
            full_text = '. '.join(sentences)
            logger.info(f"Processing text: {len(full_text)} characters")
            
            message = {
                "type": "user_input",
                "text": full_text,
                "mode": "narrate"
            }
            
            logger.info("Sending narration request...")
            await self.ws.send(json.dumps(message))
            
            audio_chunks = []
            audio_data = bytearray()
            
            while True:
                response = await self.ws.recv()
                response_data = json.loads(response)
                
                if response_data["type"] == "audio_output":
                    chunk = base64.b64decode(response_data["data"])
                    audio_chunks.append(chunk)
                    audio_data.extend(chunk)
                    logger.info(f"Received audio chunk {len(audio_chunks)} ({len(chunk)} bytes)")
                
                elif response_data["type"] == "assistant_end":
                    logger.info("Audio generation complete")
                    break
                
                elif response_data["type"] == "error":
                    error_msg = response_data.get('message', 'Unknown error')
                    logger.error(f"Error from EVI: {error_msg}")
                    break
            
            if audio_chunks:
                filename = f"paragraph_audio_{int(time.time())}.wav"
                filepath = os.path.join(self.audio_dir, filename)
                
                # Create WAV file with proper headers
                with wave.open(filepath, 'wb') as wav_file:
                    # Set WAV parameters (typical for speech audio)
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(24000)  # 24kHz sample rate
                    
                    # Write combined audio data
                    wav_file.writeframes(audio_data)
                
                logger.info(f"Saved complete audio file {filename} ({len(audio_data)} bytes)")
                return f"/static/audio/{filename}"
            
            logger.warning("No audio chunks received")
            return None
            
        except Exception as e:
            logger.error(f"Error in audio generation: {str(e)}")
            return None
        finally:
            if hasattr(self, 'ws'):
                logger.info("Closing WebSocket connection")
                await self.ws.close()

    def generate_audio(self, text):
        try:
            logger.info("Starting audio generation process")
            result = asyncio.run(self._generate_audio_async(text))
            if result:
                logger.info("Audio generation completed successfully")
            else:
                logger.warning("Audio generation completed but no audio was produced")
            return result
        except Exception as e:
            logger.error(f"Error in generate_audio: {str(e)}")
            return None
