import os
from quart import Quart, render_template, request, jsonify, Response
from quart_schema import QuartSchema
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
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
import base64
import asyncio
from hume import HumeClient
import contextlib

class Base(DeclarativeBase):
    pass

app = Quart(__name__)
app.config.from_object(Config)
QuartSchema(app)

# Initialize clients
groq_client = groq.Groq(api_key=app.config['GROQ_API_KEY'])
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

async def generate_audio_for_paragraph(paragraph):
    try:
        app.logger.info(f"Generating audio for paragraph: {paragraph[:50]}...")
        
        if not app.config.get('HUME_API_KEY') or not app.config.get('HUME_SECRET_KEY'):
            app.logger.error("Hume AI API key or secret key not configured")
            return None

        # Initialize Hume client
        client = HumeClient(api_key=app.config['HUME_API_KEY'])
        
        # Send text for narration
        socket = await client.empathic_voice.chat.connect()
        await socket.send_user_input(paragraph)
        
        async for response in socket.receive():
            if response.type == 'audio_output':
                # Save audio file
                audio_dir = os.path.join('static', 'audio')
                os.makedirs(audio_dir, exist_ok=True)
                
                filename = f"paragraph_audio_{int(time.time())}.wav"
                filepath = os.path.join(audio_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.audio)
                
                app.logger.info(f"Audio generated successfully: {filename}")
                return f"/static/audio/{filename}"
        
        app.logger.error("No audio response received")
        return None
            
    except Exception as e:
        app.logger.error(f"Error generating audio: {str(e)}")
        return None

async def generate_image_for_paragraph(paragraph):
    try:
        app.logger.info(f"Attempting to generate image for paragraph: {paragraph[:50]}...")
        
        # Check rate limit
        current_time = datetime.now()
        while image_generation_queue and current_time - image_generation_queue[0] > timedelta(seconds=IMAGE_RATE_LIMIT):
            image_generation_queue.popleft()
        
        if len(image_generation_queue) >= 6:
            wait_time = (image_generation_queue[0] + timedelta(seconds=IMAGE_RATE_LIMIT) - current_time).total_seconds()
            app.logger.info(f"Rate limit reached. Waiting for {wait_time:.2f} seconds...")
            await asyncio.sleep(wait_time)
        
        image_response = await together_client.images.generate(
            prompt=f"An image representing: {paragraph[:100]}",
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
async def index():
    return await render_template('index.html')

@app.route('/update_paragraph', methods=['POST'])
async def update_paragraph():
    try:
        data = await request.get_json()
        text = data.get('text')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        # Generate new image and audio
        async with app.app_context():
            image_url = await generate_image_for_paragraph(text)
            audio_url = await generate_audio_for_paragraph(text)
        
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
async def regenerate_image():
    try:
        data = await request.get_json()
        text = data.get('text')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        async with app.app_context():    
            image_url = await generate_image_for_paragraph(text)
        
        return jsonify({
            'success': True,
            'image_url': image_url
        })
    except Exception as e:
        app.logger.error(f"Error regenerating image: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/regenerate_audio', methods=['POST'])
async def regenerate_audio():
    try:
        data = await request.get_json()
        text = data.get('text')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        async with app.app_context():
            audio_url = await generate_audio_for_paragraph(text)
        
        return jsonify({
            'success': True,
            'audio_url': audio_url
        })
    except Exception as e:
        app.logger.error(f"Error regenerating audio: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate_story', methods=['POST'])
async def generate_story():
    async def generate():
        try:
            # Get request data outside the generator
            form_data = await request.form
            prompt = form_data.get('prompt')
            genre = form_data.get('genre')
            mood = form_data.get('mood')
            target_audience = form_data.get('target_audience')
            paragraphs = int(form_data.get('paragraphs', 5))
            
            # Now we can yield messages
            yield send_json_message('log', "Starting story generation...")
            
            system_message = f"You are a creative storyteller specializing in {genre} stories with a {mood} mood for a {target_audience} audience. Write a story based on the given prompt."
            
            yield send_json_message('log', f"Generating story text using Groq API with prompt: '{prompt}'")
            
            async with app.app_context():
                # Generate the story
                response = await groq_client.chat.completions.acreate(
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
                
                async with app.app_context():
                    # Generate image
                    yield send_json_message('log', f"Generating image for paragraph {index}...")
                    image_url = await generate_image_for_paragraph(paragraph)
                    yield send_json_message('log', f"Image generated for paragraph {index}")
                    
                    # Generate audio
                    yield send_json_message('log', f"Generating audio for paragraph {index}...")
                    audio_url = await generate_audio_for_paragraph(paragraph)
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
                
            yield send_json_message('complete', "Story generation complete!")
            
        except Exception as e:
            app.logger.error(f"Error generating story: {str(e)}")
            yield send_json_message('error', str(e))

    return Response(generate(), mimetype='text/event-stream')

@app.route('/save_story', methods=['POST'])
async def save_story():
    return jsonify({'success': True})

@app.before_serving
async def startup():
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
