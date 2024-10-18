import os
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
import urllib.parse
from config import Config
import groq
import together

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
together.api_key = app.config['TOGETHER_AI_API_KEY']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_story', methods=['POST'])
def generate_story():
    prompt = request.form.get('prompt')
    
    # Generate story using Groq API with llama-3.1-8b-instant model
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a creative storyteller. Write engaging stories."},
                {"role": "user", "content": f"Write a short story based on this prompt: {prompt}"}
            ],
            temperature=0.7,
        )
        story = response.choices[0].message.content
    except Exception as e:
        app.logger.error(f"Error generating story: {str(e)}")
        return jsonify({'error': 'Failed to generate story'}), 500

    # Generate image using Together.ai
    try:
        image_response = together.Image.create(
            prompt=f"An image representing the story: {prompt}",
            model="stable-diffusion-xl-1024-v1-0",
            width=1024,
            height=1024,
            steps=50,
            seed=42
        )
        image_url = image_response['output']['image']
    except Exception as e:
        app.logger.error(f"Error generating image: {str(e)}")
        image_url = 'https://example.com/image.jpg'  # Fallback image URL

    # TODO: Implement text-to-speech using Gemini

    return jsonify({
        'story': story,
        'image_url': image_url,
        'audio_url': 'https://example.com/audio.mp3'  # Placeholder
    })

@app.route('/save_story', methods=['POST'])
def save_story():
    # TODO: Implement story saving logic using Supabase
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
