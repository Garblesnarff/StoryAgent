import os
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, session
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_session import Session
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
app.secret_key = os.urandom(24)  # Add secret key for session management
app.config['SESSION_TYPE'] = 'filesystem'  # Configure session type
Session(app)  # Initialize Flask-Session

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

@app.route('/review')
def review():
    return render_template('review.html')

@app.route('/display')
def display():
    return render_template('display.html')

@app.route('/generate_story', methods=['POST'])
def generate_story():
    def generate():
        try:
            # Clear any existing story data
            session.clear()
            
            prompt = request.form.get('prompt')
            genre = request.form.get('genre')
            mood = request.form.get('mood')
            target_audience = request.form.get('target_audience')
            paragraphs = int(request.form.get('paragraphs', 5))
            
            yield send_json_message('log', "Starting story generation...")
            
            story_paragraphs = text_service.generate_story(
                prompt, genre, mood, target_audience, paragraphs)
            
            if not story_paragraphs:
                raise Exception("Failed to generate story")
            
            # Store story data in session
            session['story_paragraphs'] = story_paragraphs
            session.modified = True  # Ensure session is saved
            
            yield send_json_message('log', f"Story generated successfully")
            
            for index, paragraph in enumerate(story_paragraphs):
                paragraph_data = {
                    'text': paragraph,
                    'index': index
                }
                yield send_json_message('paragraph', paragraph_data)
            
            yield send_json_message('complete', "Story generation complete!")
            
        except Exception as e:
            app.logger.error(f"Error generating story: {str(e)}")
            yield send_json_message('error', str(e))

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/bring_to_life', methods=['POST'])
def bring_to_life():
    def generate():
        try:
            story_paragraphs = session.get('story_paragraphs', [])
            if not story_paragraphs:
                raise Exception("No story found in session")
            
            total_paragraphs = len(story_paragraphs)
            
            # Process each paragraph and generate media
            for index, paragraph in enumerate(story_paragraphs):
                progress = ((index + 1) / total_paragraphs * 100)
                yield send_json_message('log', f"Processing paragraph {index + 1}/{total_paragraphs} ({progress:.0f}% complete)")
                
                # Generate image
                yield send_json_message('log', f"Generating image for paragraph {index + 1}...")
                image_url = image_service.generate_image(paragraph)
                yield send_json_message('log', f"Image generated for paragraph {index + 1}")
                
                # Generate audio
                yield send_json_message('log', f"Generating audio for paragraph {index + 1}...")
                audio_url = audio_service.generate_audio(paragraph)
                yield send_json_message('log', f"Audio generated for paragraph {index + 1}")
                
                # Send complete paragraph data
                paragraph_data = {
                    'text': paragraph,
                    'image_url': image_url or 'https://example.com/fallback-image.jpg',
                    'audio_url': audio_url or '',
                    'index': index
                }
                yield send_json_message('paragraph', paragraph_data)
                
                sys.stdout.flush()
            
            session['current_step'] = 'display'
            session.modified = True
            yield send_json_message('complete', "Media generation complete!")
            
        except Exception as e:
            app.logger.error(f"Error generating media: {str(e)}")
            yield send_json_message('error', str(e))

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/update_paragraph', methods=['POST'])
def update_paragraph():
    try:
        data = request.get_json()
        text = data.get('text')
        index = data.get('index')
        
        if text is None or index is None:
            return jsonify({'error': 'Missing required data'}), 400
        
        # Update the paragraph in session
        story_paragraphs = session.get('story_paragraphs', [])
        if 0 <= index < len(story_paragraphs):
            story_paragraphs[index] = text
            session['story_paragraphs'] = story_paragraphs
            session.modified = True
            
            return jsonify({
                'success': True,
                'text': text
            })
        else:
            return jsonify({'error': 'Invalid paragraph index'}), 400
            
    except Exception as e:
        app.logger.error(f"Error updating paragraph: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/save_story', methods=['POST'])
def save_story():
    # TODO: Implement story saving logic using database
    return jsonify({'success': True})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
