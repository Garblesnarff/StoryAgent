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
from collections import deque
from datetime import datetime, timedelta
import json
import sys
import requests

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

# Rate limiting for image generation
image_generation_queue = deque(maxlen=6)
IMAGE_RATE_LIMIT = 60  # 60 seconds (1 minute)

# Hume API configuration
HUME_API_URL = 'https://api.hume.ai/v1/evi-2/narrate'
HUME_API_KEY = os.environ.get('HUME_API_KEY')
HUME_CONFIG_ID = os.environ.get('HUME_CONFIG_ID')

def send_json_message(message_type, message_data):
    """Helper function to ensure consistent JSON message formatting"""
    return json.dumps({
        'type': message_type,
        'message' if isinstance(message_data, str) else 'data': message_data
    }) + '\n'

def generate_audio_for_paragraph(paragraph):
    try:
        app.logger.info(f"Generating audio for paragraph: {paragraph[:50]}...")
        audio_dir = os.path.join('static', 'audio')
        os.makedirs(audio_dir, exist_ok=True)

        # Set up the Hume API request
        headers = {
            'Authorization': f'Bearer {HUME_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Define the payload with proper parameters
        payload = {
            'text': paragraph,
            'config_id': HUME_CONFIG_ID
        }

        # Make request to Hume API with proper error handling
        app.logger.info("Sending request to Hume API...")
        response = requests.post(HUME_API_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            app.logger.error(f"Hume API error: {response.status_code} - {response.text}")
            return None

        # Extract the audio URL from the response
        response_data = response.json()
        app.logger.info(f"Hume API response: {response_data}")
        audio_url = response_data.get('audio_url')
        
        if not audio_url:
            app.logger.error("No audio URL in response")
            app.logger.error(f"Full response: {response_data}")
            return None

        # Download the audio file from the URL
        app.logger.info(f"Downloading audio from {audio_url}")
        audio_response = requests.get(audio_url)
        if audio_response.status_code != 200:
            app.logger.error(f"Failed to download audio: {audio_response.status_code}")
            return None
            
        # Generate unique filename and save
        filename = f"paragraph_audio_{int(time.time())}.mp3"
        filepath = os.path.join(audio_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(audio_response.content)
        
        app.logger.info(f"Audio generated successfully: {filename}")
        return f"/static/audio/{filename}"

    except Exception as e:
        app.logger.error(f"Error generating audio: {str(e)}")
        app.logger.exception("Full traceback:")
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
