import os
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
import urllib.parse
from config import Config
import groq
from together import Together
import time
import tempfile
import shutil
from collections import deque
from datetime import datetime, timedelta
import json
import sys
import base64
import asyncio
import wave
from dotenv import load_dotenv
from hume import AsyncHumeClient
from hume.empathic_voice.chat.socket_client import ChatConnectOptions, ChatWebsocketConnection
from hume.empathic_voice.chat.types import SubscribeEvent
from hume.empathic_voice.types import AudioOutput

# Load environment variables
load_dotenv()

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    import models
    db.create_all()

# Initialize API clients
groq_client = groq.Groq(api_key=app.config['GROQ_API_KEY'])
together_client = Together(api_key=os.environ.get('TOGETHER_AI_API_KEY'))
hume_client = AsyncHumeClient(api_key=os.environ.get('HUME_API_KEY'))

# Rate limiting for image generation
image_generation_queue = deque(maxlen=6)
IMAGE_RATE_LIMIT = 60  # 60 seconds (1 minute)

class WebSocketInterface:
    def __init__(self):
        self.socket = None
        self.audio_data = None
        self.is_connected = False
        self.error = None
        self.received_data = None
        
    def set_socket(self, socket: ChatWebsocketConnection):
        self.socket = socket
        
    async def on_open(self):
        self.is_connected = True
        self.error = None
        
    async def on_message(self, data: SubscribeEvent):
        try:
            if isinstance(data, AudioOutput):
                # Get audio data from the event
                audio_data = data.audio if hasattr(data, 'audio') else getattr(data, 'audio_bytes', None)
                if not audio_data:
                    raise ValueError("No audio data found in the message")
                
                # Write audio data to temp file with WAV format
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                    tmp.write(audio_data)
                    tmp.flush()
                    self.received_data = tmp.name
                    return tmp.name
        except Exception as e:
            self.error = str(e)
            app.logger.error(f"Error in WebSocket on_message: {str(e)}")
            
    async def on_close(self):
        self.is_connected = False
        
    async def on_error(self, error: Exception):
        self.error = str(error)
        self.is_connected = False

async def generate_audio_with_evi(text):
    try:
        websocket_interface = WebSocketInterface()
        options = ChatConnectOptions(
            config_id=os.environ.get('HUME_CONFIG_ID'),
            secret_key=os.environ.get('HUME_SECRET_KEY'),
            config={
                "evi_version": "2",
                "name": "EVI 2 config",
                "voice": {
                    "provider": "HUME_AI",
                    "name": "DACHER"
                }
            }
        )
        
        async with hume_client.connect_with_callbacks(
            options=options,
            on_open=websocket_interface.on_open,
            on_message=websocket_interface.on_message,
            on_close=websocket_interface.on_close,
            on_error=websocket_interface.on_error
        ) as socket:
            websocket_interface.set_socket(socket)
            
            # Wait for connection
            start_time = time.time()
            while not websocket_interface.is_connected and (time.time() - start_time) < 10:
                await asyncio.sleep(0.1)
                
            if not websocket_interface.is_connected:
                raise Exception("Failed to establish WebSocket connection")
            
            # Send text to be converted to speech
            await socket.send_text(text)
            
            # Wait for audio response
            start_time = time.time()
            while not websocket_interface.received_data and (time.time() - start_time) < 30:
                if websocket_interface.error:
                    raise Exception(websocket_interface.error)
                await asyncio.sleep(0.1)
                
            if not websocket_interface.received_data:
                raise Exception("No audio response received")
            
            # Move audio file to static directory with WAV format
            timestamp = int(time.time())
            output_path = f'static/audio/paragraph_audio_{timestamp}.wav'
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Ensure WAV format and headers
            with wave.open(websocket_interface.received_data, 'rb') as wav_in:
                with wave.open(output_path, 'wb') as wav_out:
                    wav_out.setnchannels(wav_in.getnchannels())
                    wav_out.setsampwidth(wav_in.getsampwidth())
                    wav_out.setframerate(wav_in.getframerate())
                    wav_out.writeframes(wav_in.readframes(wav_in.getnframes()))
            
            os.remove(websocket_interface.received_data)  # Clean up temp file
            return f'/static/audio/paragraph_audio_{timestamp}.wav'
            
    except Exception as e:
        app.logger.error(f"Error generating audio: {str(e)}")
        return None

def generate_audio_for_paragraph(paragraph):
    try:
        # Create a new event loop for each request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(generate_audio_with_evi(paragraph))
        finally:
            loop.close()
    except Exception as e:
        app.logger.error(f"Error in generate_audio_for_paragraph: {str(e)}")
        return None

def send_json_message(message_type, message_data):
    """Helper function to ensure consistent JSON message formatting"""
    return json.dumps({
        'type': message_type,
        'message' if isinstance(message_data, str) else 'data': message_data
    }) + '\n'

def generate_image_for_paragraph(paragraph):
    try:
        app.logger.info(f"Attempting to generate image for paragraph: {paragraph[:50]}...")
        
        # Check rate limit
        current_time = datetime.now()
        while image_generation_queue and current_time - image_generation_queue[0] > timedelta(seconds=IMAGE_RATE_LIMIT):
            image_generation_queue.popleft()
        
        if len(image_generation_queue) >= 6:
            wait_time = (image_generation_queue[0] + timedelta(seconds=IMAGE_RATE_LIMIT) - current_time).total_seconds()
            app.logger.info(f"Rate limit reached. Waiting for {wait_time:.2f} seconds...")
            time.sleep(wait_time)
        
        image_response = together_client.images.generate(
            prompt=f"An image representing: {paragraph[:100]}",  # Use first 100 characters as prompt
            model="black-forest-labs/FLUX.1-schnell-Free",
            width=512,
            height=512,
            steps=4,
            n=1,
            response_format="b64_json"
        )
        
        if image_response and hasattr(image_response, 'data') and image_response.data:
            image_b64 = image_response.data[0].b64_json
            
            # Add timestamp to queue
            image_generation_queue.append(datetime.now())
            
            app.logger.info("Image generated successfully")
            return f"data:image/png;base64,{image_b64}"
        else:
            app.logger.error("No image data received from API")
            return None
    except Exception as e:
        app.logger.error(f"Error generating image: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_paragraph', methods=['POST'])
def update_paragraph():
    try:
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        # Generate new image and audio
        image_url = generate_image_for_paragraph(text)
        audio_url = generate_audio_for_paragraph(text)
        
        return jsonify({
            'success': True,
            'text': text,
            'image_url': image_url,
            'audio_url': audio_url
        })
    except Exception as e:
        app.logger.error(f"Error updating paragraph: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/regenerate_image', methods=['POST'])
def regenerate_image():
    try:
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        image_url = generate_image_for_paragraph(text)
        
        return jsonify({
            'success': True,
            'image_url': image_url
        })
    except Exception as e:
        app.logger.error(f"Error regenerating image: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/regenerate_audio', methods=['POST'])
def regenerate_audio():
    try:
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        audio_url = generate_audio_for_paragraph(text)
        
        return jsonify({
            'success': True,
            'audio_url': audio_url
        })
    except Exception as e:
        app.logger.error(f"Error regenerating audio: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate_story', methods=['POST'])
def generate_story():
    def generate():
        try:
            prompt = request.form.get('prompt')
            genre = request.form.get('genre')
            mood = request.form.get('mood')
            target_audience = request.form.get('target_audience')
            paragraphs = int(request.form.get('paragraphs', 5))
            
            yield send_json_message('log', "Starting story generation...")
            
            # Adjust the system message based on the parameters
            system_message = f"You are a creative storyteller specializing in {genre} stories with a {mood} mood for a {target_audience} audience. Write a story based on the given prompt."
            
            yield send_json_message('log', f"Generating story text using Groq API with prompt: '{prompt}'")
            
            # Generate the story
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Write a {genre} story with a {mood} mood for a {target_audience} audience based on this prompt: {prompt}. The story should be exactly {paragraphs} paragraphs long."}
                ],
                temperature=0.7,
            )
            
            if not response or not response.choices:
                raise Exception("No response from story generation API")
                
            story = response.choices[0].message.content
            if not story:
                raise Exception("Empty response from story generation API")
                
            yield send_json_message('log', f"Story text generated successfully ({len(story.split())} words)")

            # Split the story into paragraphs
            story_paragraphs = [p for p in story.split('\n\n') if p.strip()][:paragraphs]
            total_paragraphs = len(story_paragraphs)
            
            yield send_json_message('log', f"Processing {total_paragraphs} paragraphs...")
            
            # Process each paragraph and stream results
            for index, paragraph in enumerate(story_paragraphs, 1):
                if not paragraph.strip():
                    continue
                    
                progress = (index/total_paragraphs*100)
                yield send_json_message('log', f"Processing paragraph {index}/{total_paragraphs} ({progress:.0f}% complete)")
                
                # Generate image
                yield send_json_message('log', f"Generating image for paragraph {index}...")
                
                # Check rate limit before generating image
                current_time = datetime.now()
                if image_generation_queue and len(image_generation_queue) >= 6:
                    wait_time = (image_generation_queue[0] + timedelta(seconds=IMAGE_RATE_LIMIT) - current_time).total_seconds()
                    if wait_time > 0:
                        yield send_json_message('log', f"Waiting for rate limit ({wait_time:.0f} seconds)...")
                        time.sleep(wait_time)
                
                image_url = generate_image_for_paragraph(paragraph)
                yield send_json_message('log', f"Image generated for paragraph {index}")
                
                # Generate audio
                yield send_json_message('log', f"Generating audio for paragraph {index}...")
                audio_url = generate_audio_for_paragraph(paragraph)
                yield send_json_message('log', f"Audio generated for paragraph {index}")
                
                # Send paragraph data
                paragraph_data = {
                    'text': paragraph,
                    'image_url': image_url or 'https://example.com/fallback-image.jpg',
                    'audio_url': audio_url or '',
                    'index': index - 1
                }
                yield send_json_message('paragraph', paragraph_data)
                yield send_json_message('log', f"Paragraph {index} complete")

                # Ensure stream is flushed
                sys.stdout.flush()
                
            yield send_json_message('complete', "Story generation complete!")
            
        except Exception as e:
            app.logger.error(f"Error generating story: {str(e)}")
            yield send_json_message('error', str(e))

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/save_story', methods=['POST'])
def save_story():
    # TODO: Implement story saving logic using Supabase
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
