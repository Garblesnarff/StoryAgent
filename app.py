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

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    import models
    db.create_all()

# Initialize Groq client
groq_client = groq.Groq(api_key=app.config['GROQ_API_KEY'])

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

def create_log_line(prompt):
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a creative storyteller. Create a Blake Snyder's Log Line based on the given prompt."},
                {"role": "user", "content": f"Create a Blake Snyder's Log Line for this prompt: {prompt}"}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        app.logger.error(f"Error creating log line: {str(e)}")
        raise

def expand_synopsis(log_line):
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a creative storyteller. Expand the given log line into a full synopsis."},
                {"role": "user", "content": f"Expand this log line into a full synopsis: {log_line}"}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        app.logger.error(f"Error expanding synopsis: {str(e)}")
        raise

def develop_story_structure(synopsis):
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a creative storyteller. Develop a 5-act story structure from the given synopsis, with at least 3 chapters per act and at least 3 scenes per chapter."},
                {"role": "user", "content": f"Develop a 5-act story structure from this synopsis, with at least 3 chapters per act and at least 3 scenes per chapter: {synopsis}"}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        app.logger.error(f"Error developing story structure: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_story', methods=['POST'])
def generate_story():
    prompt = request.form.get('prompt')
    
    try:
        # Step 1: Create a Blake Snyder's Log Line
        log_line = create_log_line(prompt)
        
        # Step 2: Expand the Log Line into a full synopsis
        synopsis = expand_synopsis(log_line)
        
        # Step 3: Develop a 5-act story structure
        story_structure = develop_story_structure(synopsis)
        
        # Generate a short story based on the structure
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a creative storyteller. Write an engaging short story based on the given story structure."},
                {"role": "user", "content": f"Write a short story based on this story structure: {story_structure}"}
            ],
            temperature=0.7,
        )
        story = response.choices[0].message.content
    except Exception as e:
        app.logger.error(f"Error generating story: {str(e)}")
        return jsonify({'error': 'Failed to generate story'}), 500

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
        image_url = 'https://example.com/image.jpg'  # Fallback image URL

    # Generate audio using gTTS
    try:
        audio_url = generate_audio_for_scene(story)
    except Exception as e:
        app.logger.error(f"Error generating audio: {str(e)}")
        audio_url = 'https://example.com/audio.mp3'  # Fallback audio URL

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
