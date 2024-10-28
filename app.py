import os
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from sqlalchemy.orm import DeclarativeBase
import json
import sys

from services.image_generator import ImageGenerator
from services.text_generator import TextGenerator
from services.hume_audio_generator import HumeAudioGenerator
from services.regeneration_service import RegenerationService

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)
socketio = SocketIO(app)

with app.app_context():
    import models
    db.create_all()

# Initialize services
image_service = ImageGenerator()
text_service = TextGenerator()
audio_service = HumeAudioGenerator()
regeneration_service = RegenerationService(image_service, audio_service)

def send_json_message(message_type, message_data):
    """Helper function to ensure consistent JSON message formatting"""
    return json.dumps({
        'type': message_type,
        'message' if isinstance(message_data, str) else 'data': message_data
    }) + '\n'

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
        image_url = image_service.generate_image(text)
        audio_url = audio_service.generate_audio(text)
        
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
            
        image_url = regeneration_service.regenerate_image(text)
        
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
            
        audio_url = regeneration_service.regenerate_audio(text)
        
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
            
            # Generate the story
            story_paragraphs = text_service.generate_story(
                prompt, genre, mood, target_audience, paragraphs)
            
            if not story_paragraphs:
                raise Exception("Failed to generate story")
            
            total_sentences = 0
            # Count total sentences for progress tracking
            for paragraph in story_paragraphs:
                sentences = [s.strip() for s in paragraph.split('.') if s.strip()]
                total_sentences += len(sentences)
            
            yield send_json_message('log', f"Story generated with {total_sentences} sentences")
            
            current_sentence = 0
            # Process each paragraph into sentences
            for paragraph in story_paragraphs:
                sentences = [s.strip() for s in paragraph.split('.') if s.strip()]
                
                for sentence in sentences:
                    current_sentence += 1
                    progress = (current_sentence/total_sentences*100)
                    
                    # Add back the period and process the sentence
                    full_sentence = sentence + '.'
                    yield send_json_message('log', f"Processing sentence {current_sentence}/{total_sentences} ({progress:.0f}% complete)")
                    
                    # Generate image
                    yield send_json_message('log', f"Generating image for sentence {current_sentence}...")
                    image_url = image_service.generate_image(full_sentence)
                    yield send_json_message('log', f"Image generated for sentence {current_sentence}")
                    
                    # Generate audio
                    yield send_json_message('log', f"Generating audio for sentence {current_sentence}...")
                    audio_url = audio_service.generate_audio(full_sentence)
                    yield send_json_message('log', f"Audio generated for sentence {current_sentence}")
                    
                    # Send sentence data
                    sentence_data = {
                        'text': full_sentence,
                        'image_url': image_url or 'https://example.com/fallback-image.jpg',
                        'audio_url': audio_url or '',
                        'index': current_sentence - 1
                    }
                    yield send_json_message('paragraph', sentence_data)
                    
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
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
