from flask import Blueprint, render_template, request, Response, stream_with_context, session, redirect, url_for, jsonify
import sys
import json
from services.text_generator import TextGenerator
from services.image_generator import ImageGenerator
from database import db
from models import TempBookData
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

generation_bp = Blueprint('generation', __name__)
text_service = TextGenerator()
image_service = ImageGenerator()

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

@generation_bp.route('/story/regenerate_image', methods=['POST'])
def regenerate_image():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
            
        text = data['text']
        index = data.get('index')
        style = data.get('style', 'realistic')
        
        # Generate new image with style
        image_data = image_service.generate_image({
            'text': text,
            'style': style
        })
        
        if not image_data:
            return jsonify({'error': 'Failed to generate image'}), 500
            
        # Update data in appropriate storage
        if index is not None:
            story_data = session.get('story_data', {})
            temp_id = story_data.get('temp_id')
            
            if temp_id:
                # Update in temp storage
                temp_data = TempBookData.query.get(temp_id)
                if temp_data:
                    book_data = temp_data.data
                    if index < len(book_data['paragraphs']):
                        book_data['paragraphs'][index].update({
                            'image_url': image_data['image_url'],
                            'prompt': image_data['prompt'],
                            'image_style': image_data['style']
                        })
                        temp_data.data = book_data
                        db.session.commit()
            else:
                # Update in session storage
                if 'paragraphs' in story_data and index < len(story_data['paragraphs']):
                    story_data['paragraphs'][index].update({
                        'image_url': image_data['image_url'],
                        'prompt': image_data['prompt'],
                        'image_style': image_data['style']
                    })
                    session['story_data'] = story_data
        
        return jsonify({
            'success': True,
            'image_url': image_data['image_url'],
            'prompt': image_data['prompt']
        })
        
    except Exception as e:
        logger.error(f"Error regenerating image: {str(e)}")
        return jsonify({'error': str(e)}), 500

@generation_bp.route('/story/generate_cards', methods=['POST'])
def generate_cards():
    def generate():
        try:
            if 'story_data' not in session:
                raise Exception("No story data found in session")
                
            # Get story data from session or temp storage
            story_data = session['story_data']
            temp_id = story_data.get('temp_id')
            temp_data = None
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
                
                # Generate image if needed with style
                if not paragraph.get('image_url'):
                    yield send_json_message('log', f"Generating image for paragraph {index + 1}...", step='image')
                    image_data = image_service.generate_image({
                        'text': paragraph['text'],
                        'style': paragraph.get('image_style', 'realistic')
                    })
                    
                    if image_data:
                        paragraph.update({
                            'image_url': image_data['image_url'],
                            'prompt': image_data['prompt']
                        })
                    
                    # Send immediate update after image generation
                    yield send_json_message('paragraph', {
                        'text': paragraph['text'],
                        'image_url': paragraph.get('image_url'),
                        'prompt': paragraph.get('prompt'),
                        'image_style': paragraph.get('image_style', 'realistic'),
                        'index': index
                    }, step='image')
                
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
