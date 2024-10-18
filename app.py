import os
from flask import Flask, render_template, request, jsonify, session
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

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    import models
    db.create_all()

# Initialize Together AI client
together_client = Together(api_key=os.environ.get('TOGETHER_API_KEY'))

def generate_audio_for_scene(scene_content):
    # Ensure the audio directory exists
    audio_dir = os.path.join('static', 'audio')
    os.makedirs(audio_dir, exist_ok=True)
    
    # Generate audio using gTTS
    tts = gTTS(text=scene_content, lang='en')
    
    # Save the audio file
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
    
    try:
        # Generate book specification
        book_spec = generate_book_spec(prompt)
        
        # Generate story outline
        outline = generate_outline(book_spec)
        
        # Generate the first scene
        scene = generate_scene(book_spec, outline, 1, 1, 1)
        story = "\n\n".join(scene)
    except Exception as e:
        app.logger.error(f"Error generating story: {str(e)}")
        return jsonify({'error': f'Failed to generate story: {str(e)}'}), 500

    # Generate image using Together.ai
    try:
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
    except Exception as e:
        app.logger.error(f"Error generating image: {str(e)}")
        return jsonify({'error': f'Failed to generate image: {str(e)}'}), 500

    # Generate audio using gTTS
    try:
        audio_url = generate_audio_for_scene(story)
    except Exception as e:
        app.logger.error(f"Error generating audio: {str(e)}")
        return jsonify({'error': f'Failed to generate audio: {str(e)}'}), 500

    return jsonify({
        'story': story,
        'image_url': image_url,
        'audio_url': audio_url
    })

@app.route('/save_story', methods=['POST'])
def save_story():
    # TODO: Implement story saving logic using Supabase
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
