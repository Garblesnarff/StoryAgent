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

        # Initialize connection parameters with proper format
        base_url = "wss://api.hume.ai/v0/stream/cht"  # Updated endpoint
        api_key = os.environ.get('HUME_API_KEY')
        config_id = os.environ.get('HUME_CONFIG_ID')

        # Format URL with proper parameters
        params = [
            f"api_key={api_key}",
            f"config_id={config_id}",
            "stream=true"
        ]

        self.ws_url = f"{base_url}?{'&'.join(params)}"

    async def _connect(self):
        extra_headers = {
            'Authorization': f'Bearer {os.environ.get("HUME_API_KEY")}'
        }
        self.ws = await websockets.connect(
            self.ws_url,
            extra_headers=extra_headers
        )
        metadata = await self.ws.recv()
        return json.loads(metadata)

    async def _generate_audio_async(self, text):
        try:
            # Connect to websocket
            await self._connect()

            # Send the complete text for narration
            message = {
                "type": "user_input",
                "text": text
            }

            logger.info(f"Sending text for narration: {len(text)} characters")
            await self.ws.send(json.dumps(message))

            # Collect all audio data
            audio_data = bytearray()

            while True:
                response = await self.ws.recv()
                response_data = json.loads(response)

                if response_data["type"] == "audio_output":
                    chunk = base64.b64decode(response_data["data"])
                    audio_data.extend(chunk)
                    logger.info(f"Received audio chunk: {len(chunk)} bytes")

                elif response_data["type"] == "assistant_end":
                    logger.info("Received end of audio signal")
                    break

                elif response_data["type"] == "error":
                    logger.error(f"Error from EVI: {response_data.get('message', 'Unknown error')}")
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
