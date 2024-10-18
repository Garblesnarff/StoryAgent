import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from gtts import gTTS
import time
import tempfile
import logging
import base64
from together import Together
from groq import Groq

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

# Initialize Groq client
groq_client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

def generate_audio_for_scene(scene_content):
    try:
        audio_dir = os.path.join('static', 'audio')
        os.makedirs(audio_dir, exist_ok=True)
        
        tts = gTTS(text=scene_content, lang='en')
        
        filename = f"scene_audio_{int(time.time())}.mp3"
        filepath = os.path.join(audio_dir, filename)
        tts.save(filepath)
        
        return f"/static/audio/{filename}"
    except Exception as audio_error:
        app.logger.error(f"Error generating audio: {str(audio_error)}")
        return None

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

        # Generate story using GROQ API with fallback to Together AI
        app.logger.info(f"Generating story for prompt: {prompt}")
        story = generate_story_with_groq(prompt)
        app.logger.info("Story generated successfully")

        # Generate image using Together.ai
        app.logger.info("Generating image using Together.ai")
        image_url = None
        try:
            image_response = together_client.images.generate(
                prompt=f'An image representing the story: {prompt}',
                model='stabilityai/stable-diffusion-xl-base-1.0',
                width=1024,
                height=768,
                steps=30,
                seed=42,
                n=1
            )
            image_b64 = image_response.data[0].b64_json
            image_url = f'data:image/png;base64,{image_b64}'
            app.logger.info('Image generated successfully')
        except Exception as img_error:
            app.logger.error(f'Error generating image: {str(img_error)}')
            image_url = None

        # Generate audio using gTTS
        app.logger.info("Generating audio using gTTS")
        audio_url = generate_audio_for_scene(story)
        if audio_url:
            app.logger.info("Audio generated successfully")
        else:
            app.logger.warning("Audio generation failed")

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

def generate_story_with_groq(prompt):
    try:
        app.logger.info("Attempting to generate story with Groq API")
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative story writer. Generate a short story based on the given prompt."
                },
                {
                    "role": "user",
                    "content": f"Write a short story based on this prompt: {prompt}"
                }
            ],
            model="mixtral-8x7b-32768",
            max_tokens=1000
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        app.logger.error(f"Error generating story with Groq: {str(e)}")
        app.logger.info("Falling back to Together AI for story generation")
        return generate_story_with_together(prompt)

def generate_story_with_together(prompt):
    try:
        response = together_client.complete(
            prompt=f"Write a short story based on this prompt: {prompt}",
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            max_tokens=1000,
            temperature=0.7,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
            stop=["<human>", "<assistant>"]
        )
        return response['output']['text'].strip()
    except Exception as e:
        app.logger.error(f"Error generating story with Together AI: {str(e)}")
        raise ValueError("Failed to generate story with both Groq and Together AI")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
