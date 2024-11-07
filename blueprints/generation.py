from flask import Blueprint, render_template, request, Response, stream_with_context, session, redirect, url_for, jsonify
import sys
import json
from services.text_generator import TextGenerator
from services.image_generator import ImageGenerator
from services.hume_audio_generator import HumeAudioGenerator
from database import db
from models import TempBookData

generation_bp = Blueprint('generation', __name__)
text_service = TextGenerator()
image_service = ImageGenerator()
audio_service = HumeAudioGenerator()

def send_json_message(message_type, message_data, step=None):
    """Helper function to ensure consistent JSON message formatting"""
    message = {
        'type': message_type,
        'message' if isinstance(message_data, str) else 'data': message_data
    }
    if step:
        message['step'] = step
    return json.dumps(message) + '\n'

@generation_bp.route('/story/generate', methods=['GET'])
def generate():
    if 'story_data' not in session:
        return redirect(url_for('index'))
    return render_template('story/generate.html', story=session['story_data'])

@generation_bp.route('/story/generate_cards', methods=['POST'])
def generate_cards():
    def generate():
        try:
            if 'story_data' not in session:
                raise Exception("No story data found in session")
                
            # Get story data from session or temp storage
            story_data = session['story_data']
            temp_id = story_data.get('temp_id')
            if temp_id:
                temp_data = TempBookData.query.get(temp_id)
                if temp_data:
                    story_data = temp_data.data
            
            paragraphs = story_data.get('paragraphs', [])
            
            yield send_json_message('log', "Starting card generation...")
            
            for index, paragraph in enumerate(paragraphs):
                if not paragraph['text'].strip():
                    continue
                    
                progress = ((index + 1) / len(paragraphs) * 100)
                current_message = f"Processing paragraph {index + 1}/{len(paragraphs)}"
                
                # Generate image if needed
                if not paragraph.get('image_url'):
                    yield send_json_message('log', f"Generating image for paragraph {index + 1}...", step='image')
                    paragraph['image_url'] = image_service.generate_image(paragraph['text'])
                    
                    # Send immediate update after image generation
                    yield send_json_message('paragraph', {
                        'text': paragraph['text'],
                        'image_url': paragraph['image_url'],
                        'audio_url': paragraph.get('audio_url'),
                        'index': index
                    }, step='image')
                
                # Generate audio if needed
                if not paragraph.get('audio_url'):
                    yield send_json_message('log', f"Generating audio for paragraph {index + 1}...", step='audio')
                    paragraph['audio_url'] = audio_service.generate_audio(paragraph['text'])
                    
                    # Send final update after audio generation
                    yield send_json_message('paragraph', {
                        'text': paragraph['text'],
                        'image_url': paragraph['image_url'],
                        'audio_url': paragraph['audio_url'],
                        'index': index
                    }, step='audio')
                
                # Update storage
                if temp_id and temp_data:
                    temp_data.data = story_data
                    db.session.commit()
                else:
                    session['story_data'] = story_data
                
            yield send_json_message('complete', "Card generation complete!", step='complete')
            
        except Exception as e:
            yield send_json_message('error', str(e))
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')
