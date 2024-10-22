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
        app.logger.error(f"Error generating audio: {str(e)}")
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
        app.logger.error(f"Error generating image: {str(e)}")
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
        app.logger.info(f"Generating story with prompt: '{prompt}', genre: {genre}, length: {length}")
        
        # Adjust the system message based on genre and length
        system_message = f"You are a creative storyteller specializing in {genre} stories. Write a {length} story based on the given prompt."
        
        # Adjust the number of paragraphs based on the selected length
        num_paragraphs = 1 if length == 'short' else (3 if length == 'medium' else 6)
        
        app.logger.info("Calling Groq API to generate story")
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
        app.logger.info(f"Received response from Groq API. Generated {len(story.split())} words.")

        app.logger.info("Splitting story into paragraphs")
        # Split the story into paragraphs
        paragraphs = story.split('\n\n')[:num_paragraphs]  # Limit to the requested number of paragraphs
        app.logger.info(f"Split story into {len(paragraphs)} paragraphs")

        # Process each paragraph
        processed_paragraphs = []
        for index, paragraph in enumerate(paragraphs, 1):
            if paragraph.strip():  # Ignore empty paragraphs
                app.logger.info(f"Processing paragraph {index}. First few words: {' '.join(paragraph.split()[:5])}...")
                
                app.logger.info(f"Generating image for paragraph {index}")
                image_url = generate_image_for_paragraph(paragraph)
                app.logger.info(f"Image generated for paragraph {index}. URL: {image_url[:50]}...")
                
                app.logger.info(f"Generating audio for paragraph {index}")
                audio_url = generate_audio_for_paragraph(paragraph)
                app.logger.info(f"Audio generated for paragraph {index}. File: {os.path.basename(audio_url)}")
                
                processed_paragraphs.append({
                    'text': paragraph,
                    'image_url': image_url or 'https://example.com/fallback-image.jpg',
                    'audio_url': audio_url or ''
                })

        app.logger.info(f"Story generation process complete. Processed {len(processed_paragraphs)} paragraphs.")
        return jsonify({'success': True, 'paragraphs': processed_paragraphs})
    except Exception as e:
        app.logger.error(f"Error generating story: {str(e)}")
        return jsonify({'error': 'Failed to generate story', 'message': str(e)}), 500

@app.route('/save_story', methods=['POST'])
def save_story():
    # TODO: Implement story saving logic using Supabase
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
