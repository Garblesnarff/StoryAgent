import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
import urllib.parse
from config import Config
from gtts import gTTS
import time
import tempfile
from story_generator import generate_book_spec, generate_outline, generate_scene
from together import Together
import logging

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Set up logging
logging.basicConfig(level=logging.INFO)

with app.app_context():
    import models
    db.create_all()

# Initialize Together AI client
together_client = Together(api_key=os.environ.get('TOGETHER_API_KEY'))

def generate_audio_for_scene(scene_content):
    audio_dir = os.path.join('static', 'audio')
    os.makedirs(audio_dir, exist_ok=True)
    
    tts = gTTS(text=scene_content, lang='en')
    
    filename = f"scene_audio_{int(time.time())}.mp3"
    filepath = os.path.join(audio_dir, filename)
    tts.save(filepath)
    
    return f"/static/audio/{filename}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_story', methods=['POST'])
def generate_story():
    prompt = request.form.get('prompt')
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    try:
        # Check if all required API keys are available
        required_keys = ['TOGETHER_API_KEY', 'GROQ_API_KEY']
        missing_keys = [key for key in required_keys if not os.environ.get(key)]
        if missing_keys:
            raise ValueError(f"Missing required API keys: {', '.join(missing_keys)}")

        # Generate book specification
        app.logger.info(f"Generating book specification for topic: {prompt}")
        book_spec = generate_book_spec(prompt)
        app.logger.info("Book specification generated successfully")
        
        # Generate story outline
        app.logger.info("Generating story outline")
        outline = generate_outline(book_spec)
        app.logger.info("Story outline generated successfully")
        
        # Generate the first scene
        app.logger.info("Generating scene for Act 1, Chapter 1, Scene 1")
        scene = generate_scene(book_spec, outline, 1, 1, 1)
        story = "\n\n".join(scene)

        # Generate image using Together.ai
        app.logger.info("Generating image using Together.ai")
        image_response = together_client.images.generate(
            prompt=f"An image representing the story: {prompt}",
            model="black-forest-labs/FLUX.1-schnell-Free",
            width=1024,
            height=768,
            steps=4,
            n=1,
            response_format="b64_json"
        )
        image_b64 = image_response.data[0].b64_json
        image_url = f"data:image/png;base64,{image_b64}"
        app.logger.info("Image generated successfully")

        # Generate audio using gTTS
        app.logger.info("Generating audio using gTTS")
        audio_url = generate_audio_for_scene(story)
        app.logger.info("Audio generated successfully")

        return jsonify({
            'story': story,
            'image_url': image_url,
            'audio_url': audio_url
        })

    except Exception as e:
        app.logger.error(f"Error generating story: {str(e)}")
        return jsonify({'error': f'Failed to generate story: {str(e)}'}), 500

@app.route('/save_story', methods=['POST'])
def save_story():
    # TODO: Implement story saving logic using Supabase
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
