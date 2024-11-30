from gtts import gTTS
import os
import time

class AudioGenerator:
    def __init__(self):
        self.audio_dir = os.path.join('static', 'audio')
        os.makedirs(self.audio_dir, exist_ok=True)
    
    def generate_audio(self, text):
        try:
            tts = gTTS(text=text, lang='en')
            
            filename = f"paragraph_audio_{int(time.time())}.mp3"
            filepath = os.path.join(self.audio_dir, filename)
            tts.save(filepath)
            
            return f"/static/audio/{filename}"
            
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            return None
