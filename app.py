import os
import asyncio
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
import urllib.parse
from config import Config
import groq
from together import Together
import time
import tempfile
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from hume.client import AsyncHumeClient
from hume.empathic_voice.chat.socket_client import ChatConnectOptions
from hume.empathic_voice.types import UserInput
from hume.core.api_error import ApiError
import base64

# Load environment variables
load_dotenv()

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
socketio = SocketIO(app)

with app.app_context():
    import models
    db.create_all()

# Initialize Groq client
groq_client = groq.Groq(api_key=app.config['GROQ_API_KEY'])

# Initialize Together AI client
together_client = Together(api_key=os.environ.get('TOGETHER_AI_API_KEY'))

# Initialize Hume.ai client
HUME_API_KEY = os.environ.get('HUME_API_KEY')
HUME_SECRET_KEY = os.environ.get('HUME_SECRET_KEY')
HUME_CONFIG_ID = os.environ.get('HUME_CONFIG_ID')

def log_message(message, progress=None, total=None):
    app.logger.info(message)
    data = {'message': message}
    if progress is not None and total is not None:
        data['progress'] = {'current': progress, 'total': total}
    socketio.emit('log_message', data)

class WebSocketInterface:
    def __init__(self):
        self.audio_file_path = None

    def on_open(self):
        app.logger.info('WebSocket connection opened.')
    
    def on_message(self, data):
        app.logger.info('Received audio data.')
        audio_dir = os.path.join('static', 'audio')
        os.makedirs(audio_dir, exist_ok=True)
        filename = f'paragraph_audio_{int(time.time())}.wav'
        self.audio_file_path = os.path.join(audio_dir, filename)
        with open(self.audio_file_path, 'wb') as audio_file:
            audio_file.write(base64.b64decode(data['audio']))
        app.logger.info(f'Audio file saved at: {self.audio_file_path}')

    def on_close(self):
        app.logger.info('WebSocket connection closed.')
    
    def on_error(self, error):
        app.logger.error(f'Error encountered: {error}')

async def generate_audio_for_paragraph(paragraph):
    try:
        app.logger.info(f"Starting audio generation for paragraph: {paragraph[:50]}...")
        app.logger.info(f"Using HUME_API_KEY: {'*' * len(HUME_API_KEY)}")
        app.logger.info(f"Using HUME_SECRET_KEY: {'*' * len(HUME_SECRET_KEY)}")
        app.logger.info(f"Using HUME_CONFIG_ID: {HUME_CONFIG_ID}")

        client = AsyncHumeClient(api_key=HUME_API_KEY)
        options = ChatConnectOptions(config_id=HUME_CONFIG_ID, secret_key=HUME_SECRET_KEY)
        websocket_interface = WebSocketInterface()

        async with client.empathic_voice.chat.connect_with_callbacks(
            options=options,
            on_open=websocket_interface.on_open,
            on_message=websocket_interface.on_message,
            on_close=websocket_interface.on_close,
            on_error=websocket_interface.on_error
        ) as socket:
            user_input = UserInput(text=paragraph)
            await socket.send_user_input(user_input)
            
            # Wait for the audio file to be generated
            timeout = 30  # Timeout in seconds
            start_time = time.time()
            while not websocket_interface.audio_file_path and time.time() - start_time < timeout:
                await asyncio.sleep(1)
            
            if websocket_interface.audio_file_path:
                app.logger.info(f"Audio file generated successfully: {websocket_interface.audio_file_path}")
                return f"/static/audio/{os.path.basename(websocket_interface.audio_file_path)}"
            else:
                app.logger.error("Audio file path is None after generation attempt")
                return ""

    except ApiError as e:
        app.logger.error(f"Hume API error occurred: {e}")
        return ""
    except Exception as e:
        app.logger.error(f"Unexpected error in audio generation: {e}")
        return ""

def generate_image_for_paragraph(paragraph):
    try:
        image_response = together_client.images.generate(
            prompt=f"An image representing: {paragraph[:100]}",  # Use first 100 characters as prompt
            model="black-forest-labs/FLUX.1-schnell-Free",
            width=512,
            height=512,
            steps=4,
            n=1,
            response_format="b64_json"
        )
        image_b64 = image_response.data[0].b64_json
        return f"data:image/png;base64,{image_b64}"
    except Exception as e:
        app.logger.error(f"Error generating image: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_story', methods=['POST'])
async def generate_story():
    prompt = request.form.get('prompt')
    
    try:
        app.logger.debug('Starting story generation')
        log_message('Starting story generation process')
        log_message(f'Received prompt: {prompt[:50]}...')
        
        log_message("Calling Groq API to generate story")
        # Generate the first scene of the first chapter
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a creative storyteller. Write the first scene of the first chapter based on the given prompt."},
                {"role": "user", "content": f"Write the first scene of a story based on this prompt: {prompt}"}
            ],
            temperature=0.7,
        )
        scene = response.choices[0].message.content
        app.logger.debug(f'Groq API response: {scene[:100]}...')  # Log first 100 characters
        log_message(f"Received response from Groq API. Generated {len(scene.split())} words.")

        log_message("Splitting scene into paragraphs")
        # Split the scene into paragraphs
        paragraphs = scene.split('\n\n')
        total_paragraphs = len(paragraphs)
        log_message(f"Split scene into {total_paragraphs} paragraphs")

        # Emit the total number of paragraphs
        socketio.emit('total_paragraphs', {'total': total_paragraphs})

        # Process each paragraph
        for index, paragraph in enumerate(paragraphs):
            if paragraph.strip():  # Ignore empty paragraphs
                app.logger.debug(f'Processing paragraph {index + 1}')
                log_message(f"Processing paragraph {index + 1} of {total_paragraphs}. First few words: {' '.join(paragraph.split()[:5])}...", progress=index + 1, total=total_paragraphs)
                
                log_message(f"Generating image for paragraph {index + 1}", progress=index + 1, total=total_paragraphs)
                image_url = generate_image_for_paragraph(paragraph)
                if image_url:
                    app.logger.debug(f'Generated image URL: {image_url[:50]}...')
                    log_message(f"Image generated for paragraph {index + 1}. URL: {image_url[:50]}...", progress=index + 1, total=total_paragraphs)
                else:
                    log_message(f"Failed to generate image for paragraph {index + 1}", progress=index + 1, total=total_paragraphs)
                
                log_message(f"Generating audio for paragraph {index + 1}", progress=index + 1, total=total_paragraphs)
                audio_url = await generate_audio_for_paragraph(paragraph)
                if audio_url:
                    app.logger.debug(f'Generated audio URL: {audio_url}')
                    log_message(f"Audio generated for paragraph {index + 1}. File: {os.path.basename(audio_url)}", progress=index + 1, total=total_paragraphs)
                else:
                    log_message(f"Failed to generate audio for paragraph {index + 1}", progress=index + 1, total=total_paragraphs)
                
                # Emit the paragraph data to the client
                socketio.emit('new_paragraph', {
                    'text': paragraph,
                    'image_url': image_url or 'https://example.com/fallback-image.jpg',
                    'audio_url': audio_url or ''
                })

        app.logger.debug('Story generation complete')
        log_message(f"Story generation process complete. Processed {total_paragraphs} paragraphs.")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error generating story: {str(e)}")
        log_message(f"Error generating story: {str(e)}")
        return jsonify({'error': 'Failed to generate story', 'message': str(e)}), 500

@app.route('/save_story', methods=['POST'])
def save_story():
    # TODO: Implement story saving logic using Supabase
    return jsonify({'success': True})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, debug=True)
