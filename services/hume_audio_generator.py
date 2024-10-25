from hume import HumeStreamClient
import os
import time
import asyncio

class HumeAudioGenerator:
    def __init__(self):
        self.audio_dir = os.path.join('static', 'audio')
        os.makedirs(self.audio_dir, exist_ok=True)
        self.client = HumeStreamClient(api_key=os.environ.get('HUME_API_KEY', ''))
    
    def generate_audio(self, text):
        try:
            # Run async code in sync context
            return asyncio.run(self._generate_audio_async(text))
        except Exception as e:
            print(f"Error generating audio with Hume: {str(e)}")
            return None

    async def _generate_audio_async(self, text):
        try:
            configs = [{"voice": {"language": "en"}}]
            async with self.client.connect(configs) as socket:
                # Generate speech
                result = await socket.voice.generate_speech(text)
                
                # Save audio file
                filename = f"paragraph_audio_{int(time.time())}.wav"
                filepath = os.path.join(self.audio_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(result.audio)
                
                return f"/static/audio/{filename}"
            
        except Exception as e:
            print(f"Error generating audio with Hume: {str(e)}")
            return None
