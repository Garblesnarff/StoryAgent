import os
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from sqlalchemy.orm import DeclarativeBase
import json
import sys
import logging

from services.image_generator import ImageGenerator
from services.text_generator import TextGenerator
from services.hume_audio_generator import HumeAudioGenerator
from services.regeneration_service import RegenerationService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.info("Received sentence update request")
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            logger.warning("No text provided in update request")
            return jsonify({'error': 'No text provided'}), 400
            
        logger.info("Generating new image and audio for updated sentence")
        # Generate new image and audio
        image_url = image_service.generate_image(text)
        audio_url = audio_service.generate_audio(text)
        
        logger.info("Successfully updated sentence with new content")
        return jsonify({
            'success': True,
            'text': text,
            'image_url': image_url,
            'audio_url': audio_url
        })
    except Exception as e:
        logger.error(f"Error updating sentence: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/regenerate_image', methods=['POST'])
def regenerate_image():
    try:
        logger.info("Received image regeneration request")
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            logger.warning("No text provided for image regeneration")
            return jsonify({'error': 'No text provided'}), 400
            
        image_url = regeneration_service.regenerate_image(text)
        logger.info("Successfully regenerated image")
        
        return jsonify({
            'success': True,
            'image_url': image_url
        })
    except Exception as e:
        logger.error(f"Error regenerating image: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/regenerate_audio', methods=['POST'])
def regenerate_audio():
    try:
        logger.info("Received audio regeneration request")
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            logger.warning("No text provided for audio regeneration")
            return jsonify({'error': 'No text provided'}), 400
            
        audio_url = regeneration_service.regenerate_audio(text)
        logger.info("Successfully regenerated audio")
        
        return jsonify({
            'success': True,
            'audio_url': audio_url
        })
    except Exception as e:
        logger.error(f"Error regenerating audio: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate_story', methods=['POST'])
def generate_story():
    def generate():
        try:
            # Log initial parameters received
            yield send_json_message('log', "Initializing story generation...")
            yield send_json_message('log', "Processing story parameters...")
            
            prompt = request.form.get('prompt')
            genre = request.form.get('genre')
            mood = request.form.get('mood')
            target_audience = request.form.get('target_audience')
            paragraphs = int(request.form.get('paragraphs', 5))  # Now represents number of sentences
            
            yield send_json_message('log', f"Creating story with {paragraphs} sentences in {genre} genre...")
            yield send_json_message('log', "Starting story generation...")
            
            # Generate the story
            story_sentences = text_service.generate_story(
                prompt, genre, mood, target_audience, paragraphs)
            
            if not story_sentences:
                raise Exception("Failed to generate story")
            
            total_sentences = len(story_sentences)
            total_words = sum(len(s.split()) for s in story_sentences)
            yield send_json_message('log', f"Story text generated successfully ({total_words} words)")
            
            # Process each sentence
            for index, sentence in enumerate(story_sentences, 1):
                if not sentence.strip():
                    continue
                    
                progress = (index/total_sentences*100)
                yield send_json_message('log', f"Processing sentence {index}/{total_sentences} ({progress:.0f}% complete)")
                
                # Generate image
                yield send_json_message('log', f"Generating image for sentence {index}...")
                image_url = image_service.generate_image(sentence)
                yield send_json_message('log', f"Image generated for sentence {index}")
                
                # Generate audio
                yield send_json_message('log', f"Generating audio for sentence {index}...")
                audio_url = audio_service.generate_audio(sentence)
                yield send_json_message('log', f"Audio generated for sentence {index}")
                
                # Send sentence data
                sentence_data = {
                    'text': sentence,
                    'image_url': image_url or 'https://example.com/fallback-image.jpg',
                    'audio_url': audio_url or '',
                    'index': index - 1
                }
                yield send_json_message('paragraph', sentence_data)
                yield send_json_message('log', f"Sentence {index} complete")
                
                # Ensure stream is flushed
                sys.stdout.flush()
                
            yield send_json_message('complete', "Story generation complete!")
            logger.info("Story generation completed successfully")
            
        except Exception as e:
            logger.error(f"Error generating story: {str(e)}")
            yield send_json_message('error', str(e))

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/save_story', methods=['POST'])
def save_story():
    # TODO: Implement story saving logic using Supabase
    return jsonify({'success': True})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
