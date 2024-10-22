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
from collections import deque
from datetime import datetime, timedelta
from flask_socketio import SocketIO, emit

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

# Rate limiting for image generation
image_generation_queue = deque(maxlen=6)
IMAGE_RATE_LIMIT = 60  # 60 seconds (1 minute)

def generate_audio_for_paragraph(paragraph):
    try:
        app.logger.info(f"Generating audio for paragraph: {paragraph[:50]}...")
        audio_dir = os.path.join('static', 'audio')
        os.makedirs(audio_dir, exist_ok=True)
        
        tts = gTTS(text=paragraph, lang='en')
        
        filename = f"paragraph_audio_{int(time.time())}.mp3"
        filepath = os.path.join(audio_dir, filename)
        tts.save(filepath)
        
        app.logger.info(f"Audio generated successfully: {filename}")
        return f"/static/audio/{filename}"
    except Exception as e:
        app.logger.error(f"Error generating audio: {str(e)}")
        return None

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
        image_b64 = image_response.data[0].b64_json
        
        # Add timestamp to queue
        image_generation_queue.append(datetime.now())
        
        app.logger.info("Image generated successfully")
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
    mood = request.form.get('mood')
    target_audience = request.form.get('target_audience')
    paragraphs = int(request.form.get('paragraphs', 5))
    
    try:
        app.logger.info(f"Generating story with prompt: '{prompt}', genre: {genre}, mood: {mood}, target audience: {target_audience}, paragraphs: {paragraphs}")
        
        # Adjust the system message based on the new parameters
        system_message = f"You are a creative storyteller specializing in {genre} stories with a {mood} mood for a {target_audience} audience. Write a story based on the given prompt."
        
        app.logger.info("Calling Groq API to generate story")
        # Generate the story
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Write a {genre} story with a {mood} mood for a {target_audience} audience based on this prompt: {prompt}. The story should be exactly {paragraphs} paragraphs long."}
            ],
            temperature=0.7,
        )
        story = response.choices[0].message.content
        app.logger.info(f"Received response from Groq API. Generated {len(story.split())} words.")

        app.logger.info("Splitting story into paragraphs")
        # Split the story into paragraphs
        story_paragraphs = story.split('\n\n')[:paragraphs]  # Limit to the requested number of paragraphs
        app.logger.info(f"Split story into {len(story_paragraphs)} paragraphs")

        # Process each paragraph
        for index, paragraph in enumerate(story_paragraphs, 1):
            if paragraph.strip():  # Ignore empty paragraphs
                app.logger.info(f"Processing paragraph {index}. First few words: {' '.join(paragraph.split()[:5])}...")
                
                app.logger.info(f"Generating image for paragraph {index}")
                image_url = generate_image_for_paragraph(paragraph)
                app.logger.info(f"Image generated for paragraph {index}. URL: {image_url[:50]}...")
                
                app.logger.info(f"Generating audio for paragraph {index}")
                audio_url = generate_audio_for_paragraph(paragraph)
                app.logger.info(f"Audio generated for paragraph {index}. File: {os.path.basename(audio_url)}")
                
                # Emit the processed paragraph to the client
                socketio.emit('paragraph_processed', {
                    'text': paragraph,
                    'image_url': image_url or 'https://example.com/fallback-image.jpg',
                    'audio_url': audio_url or ''
                })

        app.logger.info(f"Story generation process complete. Processed {len(story_paragraphs)} paragraphs.")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error generating story: {str(e)}")
        return jsonify({'error': 'Failed to generate story', 'message': str(e)}), 500

@app.route('/save_story', methods=['POST'])
def save_story():
    # TODO: Implement story saving logic using Supabase
    return jsonify({'success': True})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
