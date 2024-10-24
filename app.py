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
import base64

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
        
        # Configure Hume API request
        HUME_API_URL = "https://api.hume.ai/v0/batch/synthesize/audio"
        headers = {
            "Authorization": f"Bearer {os.environ.get('HUME_API_KEY')}",
            "Content-Type": "application/json"
        }
        
        # Create job request
        data = {
            "text": paragraph,
            "model": {
                "name": "evi-2",
                "configs": {
                    "output_format": "mp3",
                    "voice_style": "natural",
                    "speaking_rate": 1.0
                }
            }
        }
        
        # Submit job
        response = requests.post(HUME_API_URL, headers=headers, json=data)
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data['job_id']
        
        # Poll for job completion
        status_url = f"{HUME_API_URL}/{job_id}"
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            status_response = requests.get(status_url, headers=headers)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            if status_data['status'] == 'completed':
                # Get the audio URL from the completed job
                audio_url = status_data['artifacts'][0]['url']
                
                # Download the audio file
                audio_response = requests.get(audio_url)
                audio_response.raise_for_status()
                
                filename = f"paragraph_audio_{int(time.time())}.mp3"
                filepath = os.path.join(audio_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(audio_response.content)
                
                app.logger.info(f"Audio generated successfully: {filename}")
                return f"/static/audio/{filename}"
                
            elif status_data['status'] == 'failed':
                raise Exception(f"Job failed: {status_data.get('error', 'Unknown error')}")
                
            time.sleep(2)
            attempt += 1
            
        raise Exception("Job timed out")
            
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
            if not prompt:
                raise ValueError("Story prompt is required")

            genre = request.form.get('genre')
            if not genre:
                raise ValueError("Genre selection is required")

            mood = request.form.get('mood')
            if not mood:
                raise ValueError("Mood selection is required")

            target_audience = request.form.get('target_audience')
            if not target_audience:
                raise ValueError("Target audience selection is required")

            try:
                paragraphs = int(request.form.get('paragraphs', 5))
                if paragraphs < 1 or paragraphs > 10:
                    raise ValueError("Number of paragraphs must be between 1 and 10")
            except ValueError:
                raise ValueError("Invalid number of paragraphs")
            
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
            
        except ValueError as e:
            app.logger.error(f"Validation error: {str(e)}")
            yield send_json_message('error', str(e))
        except Exception as e:
            app.logger.error(f"Error generating story: {str(e)}")
            yield send_json_message('error', f"An error occurred while generating the story: {str(e)}")

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/save_story', methods=['POST'])
def save_story():
    # TODO: Implement story saving logic using Supabase
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
