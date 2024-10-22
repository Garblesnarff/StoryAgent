import os
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
import urllib.parse
from config import Config
import groq
from together import Together
from gtts import gTTS
import time
import tempfile
from flask_socketio import SocketIO
import eventlet

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
socketio = SocketIO(app, async_mode='eventlet')

with app.app_context():
    import models
    db.create_all()

# Initialize Groq client
groq_client = groq.Groq(api_key=app.config['GROQ_API_KEY'])

# Initialize Together AI client
together_client = Together(api_key=os.environ.get('TOGETHER_AI_API_KEY'))

def log_message(message, progress=None, total=None):
    app.logger.info(message)
    data = {'message': message}
    if progress is not None and total is not None:
        data['progress'] = {'current': progress, 'total': total}
    socketio.emit('log_message', data)

def generate_audio_for_paragraph(paragraph):
    try:
        audio_dir = os.path.join('static', 'audio')
        os.makedirs(audio_dir, exist_ok=True)
        
        tts = gTTS(text=paragraph, lang='en')
        
        filename = f"paragraph_audio_{int(time.time())}.mp3"
        filepath = os.path.join(audio_dir, filename)
        tts.save(filepath)
        
        return f"/static/audio/{filename}"
    except Exception as e:
        log_message(f"Error generating audio: {str(e)}")
        return None

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
        log_message(f"Error generating image: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_story', methods=['POST'])
def generate_story():
    prompt = request.form.get('prompt')
    
    try:
        log_message("Starting story generation process")
        log_message(f"Received prompt: {prompt[:50]}...")  # Log first 50 characters of prompt
        
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
                log_message(f"Processing paragraph {index + 1} of {total_paragraphs}. First few words: {' '.join(paragraph.split()[:5])}...", progress=index + 1, total=total_paragraphs)
                
                log_message(f"Generating image for paragraph {index + 1}", progress=index + 1, total=total_paragraphs)
                image_url = generate_image_for_paragraph(paragraph)
                if image_url:
                    log_message(f"Image generated for paragraph {index + 1}. URL: {image_url[:50]}...", progress=index + 1, total=total_paragraphs)
                else:
                    log_message(f"Failed to generate image for paragraph {index + 1}", progress=index + 1, total=total_paragraphs)
                
                log_message(f"Generating audio for paragraph {index + 1}", progress=index + 1, total=total_paragraphs)
                audio_url = generate_audio_for_paragraph(paragraph)
                if audio_url:
                    log_message(f"Audio generated for paragraph {index + 1}. File: {os.path.basename(audio_url)}", progress=index + 1, total=total_paragraphs)
                else:
                    log_message(f"Failed to generate audio for paragraph {index + 1}", progress=index + 1, total=total_paragraphs)
                
                # Emit the paragraph data to the client
                socketio.emit('new_paragraph', {
                    'text': paragraph,
                    'image_url': image_url or 'https://example.com/fallback-image.jpg',
                    'audio_url': audio_url or ''
                })

        log_message(f"Story generation process complete. Processed {total_paragraphs} paragraphs.")
        return jsonify({'success': True})
    except Exception as e:
        log_message(f"Error generating story: {str(e)}")
        return jsonify({'error': 'Failed to generate story', 'message': str(e)}), 500

@app.route('/save_story', methods=['POST'])
def save_story():
    # TODO: Implement story saving logic using Supabase
    return jsonify({'success': True})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)