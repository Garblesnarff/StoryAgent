import websockets
import json
import asyncio
import base64
import os
import time
from datetime import datetime
import logging
import wave

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HumeAudioGenerator:
    def __init__(self):
        self.audio_dir = os.path.join('static', 'audio')
        os.makedirs(self.audio_dir, exist_ok=True)

        # Initialize connection parameters
        self.ws_url = "wss://api.hume.ai/v0/batch/prosody"  # Changed to batch endpoint
        self.api_key = os.environ.get('HUME_API_KEY')
        self.config_id = os.environ.get('HUME_CONFIG_ID')

    async def _connect(self):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Connect with proper headers
        self.ws = await websockets.connect(
            self.ws_url,
            extra_headers=headers
        )
        return True

    async def _generate_audio_async(self, text):
        try:
            # Connect first
            await self._connect()
            
            # Prepare request payload
            request = {
                "text": text,
                "config_id": self.config_id
            }
            
            # Send request
            await self.ws.send(json.dumps(request))
            
            # Collect audio data
            audio_data = bytearray()
            
            while True:
                response = await self.ws.recv()
                response_data = json.loads(response)
                
                if response_data.get("type") == "audio":
                    chunk = base64.b64decode(response_data["data"])
                    audio_data.extend(chunk)
                    logger.info(f"Received audio chunk: {len(chunk)} bytes")
                elif response_data.get("type") == "complete":
                    logger.info("Audio generation complete")
                    break
                elif response_data.get("type") == "error":
                    logger.error(f"Hume API error: {response_data.get('message')}")
                    return None

            if audio_data:
                filename = f"paragraph_audio_{int(time.time())}.wav"
                filepath = os.path.join(self.audio_dir, filename)

                # Write the complete audio data as a WAV file
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
