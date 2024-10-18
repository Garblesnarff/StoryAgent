import os
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
import urllib.parse
from config import Config
import groq
from together import Together
from google.cloud import texttospeech
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

def synthesize_speech(text, output_filename):
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code='en-US', ssml_gender=texttospeech.SsmlVoiceGender.FEMALE)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
    with open(output_filename, 'wb') as out:
        out.write(response.audio_content)
    return output_filename

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

    # Generate audio using Google Cloud Text-to-Speech
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            audio_file = synthesize_speech(story, temp_file.name)
            audio_url = f"/static/temp/{os.path.basename(audio_file)}"
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
