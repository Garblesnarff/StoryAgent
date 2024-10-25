from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from sqlalchemy.orm import DeclarativeBase
import json

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
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

with app.app_context():
    import models
    db.create_all()

# Initialize services
image_service = ImageGenerator()
text_service = TextGenerator()
audio_service = HumeAudioGenerator()
regeneration_service = RegenerationService(image_service, audio_service)

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

@socketio.on('generate_story')
def handle_story_generation(data):
    try:
        prompt = data.get('prompt')
        genre = data.get('genre')
        mood = data.get('mood')
        target_audience = data.get('target_audience')
        paragraphs = int(data.get('paragraphs', 5))
        
        # Generate the story
        story_paragraphs = text_service.generate_story(
            prompt, genre, mood, target_audience, paragraphs)
        
        if not story_paragraphs:
            raise Exception("Failed to generate story")
        
        total_paragraphs = len(story_paragraphs)
        socketio.emit('log', {'message': f"Story text generated successfully"})
        
        for index, paragraph in enumerate(story_paragraphs, 1):
            if not paragraph.strip():
                continue
                
            progress = (index/total_paragraphs*100)
            socketio.emit('log', {'message': f"Processing paragraph {index}/{total_paragraphs}"})
            
            # Generate image and audio
            image_url = image_service.generate_image(paragraph)
            audio_url = audio_service.generate_audio(paragraph)
            
            # Send paragraph data
            paragraph_data = {
                'text': paragraph,
                'image_url': image_url,
                'audio_url': audio_url,
                'index': index - 1
            }
            socketio.emit('paragraph', {'data': paragraph_data})
            
        socketio.emit('complete', {'message': "Story generation complete!"})
        
    except Exception as e:
        socketio.emit('error', {'message': str(e)})

@app.route('/save_story', methods=['POST'])
def save_story():
    # TODO: Implement story saving logic using Supabase
    return jsonify({'success': True})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
