import os
from flask import Flask, render_template, request, jsonify
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
together_client = Together(api_key=os.environ.get('TOGETHER_AI_API_KEY'))

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
        print(f"Error generating audio: {str(e)}")
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
        print(f"Error generating image: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_story', methods=['POST'])
def generate_story():
    prompt = request.form.get('prompt')
    genre = request.form.get('genre')
    length = request.form.get('length')
    
    try:
        # Adjust the system message based on genre and length
        system_message = f"You are a creative storyteller specializing in {genre} stories. Write a {length} story based on the given prompt."
        
        # Adjust the number of paragraphs based on the selected length
        num_paragraphs = 1 if length == 'short' else (3 if length == 'medium' else 6)
        
        # Generate the story
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Write a {genre} story with {num_paragraphs} paragraphs based on this prompt: {prompt}"}
            ],
            temperature=0.7,
        )
        story = response.choices[0].message.content

        # Split the story into paragraphs
        paragraphs = story.split('\n\n')[:num_paragraphs]  # Limit to the requested number of paragraphs

        # Process each paragraph
        processed_paragraphs = []
        for paragraph in paragraphs:
            if paragraph.strip():  # Ignore empty paragraphs
                image_url = generate_image_for_paragraph(paragraph)
                audio_url = generate_audio_for_paragraph(paragraph)
                processed_paragraphs.append({
                    'text': paragraph,
                    'image_url': image_url or 'https://example.com/fallback-image.jpg',
                    'audio_url': audio_url or ''
                })

        return jsonify({'success': True, 'paragraphs': processed_paragraphs})
    except Exception as e:
        return jsonify({'error': 'Failed to generate story', 'message': str(e)}), 500

@app.route('/save_story', methods=['POST'])
def save_story():
    # TODO: Implement story saving logic using Supabase
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
