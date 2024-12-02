from flask import Blueprint, render_template, request, Response, stream_with_context, session, redirect, url_for, jsonify
import sys
import json
from services.text_generator import TextGenerator
from services.image_generator import ImageGenerator
from services.hume_audio_generator import HumeAudioGenerator
from services.prompt_generator import PromptGenerator
from database import db
from models import TempBookData
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

generation_bp = Blueprint('generation', __name__)
text_service = TextGenerator()
image_service = ImageGenerator()
audio_service = HumeAudioGenerator()
prompt_generator = PromptGenerator()

def send_json_message(message_type, message_data, step=None):
    """Helper function to ensure consistent JSON message formatting"""
    message = {
        'type': message_type,
        'message' if isinstance(message_data, str) else 'data': message_data
    }
    if step:
        message['step'] = step
    return json.dumps(message).replace('\n', ' ') + '\n'

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
        
        # Generate chain of image prompts using Gemini
        story_context = session.get('story_data', {}).get('story_context', '')
        image_prompts = prompt_generator.generate_image_prompt(story_context, text, use_chain=True)
        
        # Generate new image with chained prompts
        result = image_service.generate_image_chain(image_prompts, style=style)
        if not result:
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
                        book_data['paragraphs'][index]['image_url'] = result['url']
                        book_data['paragraphs'][index]['image_prompt'] = result['prompt']
                        temp_data.data = book_data
                        db.session.commit()
            else:
                # Update in session storage
                if 'paragraphs' in story_data and index < len(story_data['paragraphs']):
                    story_data['paragraphs'][index]['image_url'] = result['url']
                    story_data['paragraphs'][index]['image_prompt'] = result['prompt']
                    session['story_data'] = story_data
        
        return jsonify({
            'success': True,
            'image_url': result['url'],
            'image_prompt': result['prompt']
        })
        
    except Exception as e:
        logger.error(f"Error regenerating image: {str(e)}")
        return jsonify({'error': str(e)}), 500

@generation_bp.route('/story/regenerate_audio', methods=['POST'])
def regenerate_audio():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
            
        text = data['text']
        index = data.get('index')
        
        # Generate new audio
        audio_url = audio_service.generate_audio(text)
        if not audio_url:
            return jsonify({'error': 'Failed to generate audio'}), 500
            
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
                        book_data['paragraphs'][index]['audio_url'] = audio_url
                        temp_data.data = book_data
                        db.session.commit()
            else:
                # Update in session storage
                if 'paragraphs' in story_data and index < len(story_data['paragraphs']):
                    story_data['paragraphs'][index]['audio_url'] = audio_url
                    session['story_data'] = story_data
        
        return jsonify({
            'success': True,
            'audio_url': audio_url
        })
        
    except Exception as e:
        logger.error(f"Error regenerating audio: {str(e)}")
        return jsonify({'error': str(e)}), 500

@generation_bp.route('/story/generate_cards', methods=['POST'])
def generate_cards():
    def generate():
        try:
            if 'story_data' not in session:
                yield send_json_message('error', 'No story data found in session')
                return
                
            data = request.get_json()
            if not data:
                yield send_json_message('error', 'Invalid request data')
                return
                
            index = data.get('index')
            text = data.get('text')
            story_context = data.get('story_context', '')
            style = data.get('style', 'realistic')
            
            if index is None or not text:
                yield send_json_message('error', 'Missing required parameters')
                return
            
            # Generate chain of image prompts using Gemini
            yield send_json_message('log', 'Generating image prompts...', step='prompt')
            image_prompts = prompt_generator.generate_image_prompt(story_context, text, use_chain=True)
            
            # Generate image with chained prompts
            yield send_json_message('log', 'Generating image through multiple steps...', step='image')
            result = image_service.generate_image_chain(image_prompts, style=style)
            
            if not result:
                yield send_json_message('error', 'Failed to generate image')
                return

            # Generate audio
            yield send_json_message('log', 'Generating audio...', step='audio')
            audio_url = audio_service.generate_audio(text)
                
            # Update storage and send response
            paragraph_data = {
                'text': text,
                'image_url': result['url'],
                'image_prompt': result.get('prompt', ''),
                'audio_url': audio_url,
                'index': index
            }
            
            story_data = session['story_data']
            temp_id = story_data.get('temp_id')
            
            if temp_id:
                temp_data = TempBookData.query.get(temp_id)
                if temp_data:
                    story_data = temp_data.data
                    story_data['paragraphs'][index]['image_url'] = result['url']
                    story_data['paragraphs'][index]['image_prompt'] = result.get('prompt', '')
                    story_data['paragraphs'][index]['audio_url'] = audio_url
                    temp_data.data = story_data
                    db.session.commit()
            else:
                story_data['paragraphs'][index]['image_url'] = result['url']
                story_data['paragraphs'][index]['image_prompt'] = result.get('prompt', '')
                story_data['paragraphs'][index]['audio_url'] = audio_url
                session['story_data'] = story_data
            
            yield send_json_message('paragraph', paragraph_data)
            yield send_json_message('complete', "Card generation complete!")
            
        except Exception as e:
            logger.error(f"Error generating cards: {str(e)}")
            yield send_json_message('error', str(e))
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')
