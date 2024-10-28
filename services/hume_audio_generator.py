import websockets
import json
import asyncio
import base64
import os
import time
from datetime import datetime

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
            
            # Send narration request
            message = {
                "type": "user_input",
                "text": text,
                "mode": "narrate"
            }
            await self.ws.send(json.dumps(message))
            
            # Handle response and save audio
            filename = None
            while True:
                response = await self.ws.recv()
                response_data = json.loads(response)
                
                if response_data["type"] == "audio_output":
                    audio_bytes = base64.b64decode(response_data["data"])
                    filename = f"paragraph_audio_{int(time.time())}.wav"
                    filepath = os.path.join(self.audio_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(audio_bytes)
                
                elif response_data["type"] == "assistant_end":
                    break
            
            await self.ws.close()
            
            if filename:
                return f"/static/audio/{filename}"
            return None
            
        except Exception as e:
            print(f"Error generating audio with Hume: {str(e)}")
            if hasattr(self, 'ws'):
                await self.ws.close()
            return None

    def generate_audio(self, text):
        try:
            return asyncio.run(self._generate_audio_async(text))
        except Exception as e:
            print(f"Error in generate_audio: {str(e)}")
            return None
