
from flask import Blueprint, request, jsonify, session
from datetime import datetime
import logging
from database import db
from models import TempBookData
from services.image_generator import ImageGenerator
from services.hume_audio_generator import HumeAudioGenerator
from services.prompt_generator import PromptGenerator
from services.text_generator import TextGenerator
import json
from flask import render_template, Response, stream_with_context, redirect, url_for

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

generation_bp = Blueprint('generation', __name__)
# Initialize services (ImageGenerator removed from here)
text_service = TextGenerator()
# image_service = ImageGenerator() # Moved inside routes
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

def log_generation_history(temp_id, index, generation_type, status, error_message=None, prompt=None, result_url=None, retries=0):
    """Helper function to log generation history"""
    try:
        from sqlalchemy import text
        query = text("""
            INSERT INTO generation_history 
            (temp_data_id, paragraph_index, generation_type, status, error_message, prompt, result_url, retries, created_at)
            VALUES (:temp_id, :index, :type, :status, :error, :prompt, :url, :retries, :timestamp)
        """)
        
        db.session.execute(
            query,
            {
                'temp_id': temp_id,
                'index': index,
                'type': generation_type,
                'status': status,
                'error': error_message,
                'prompt': prompt,
                'url': result_url,
                'retries': retries,
                'timestamp': datetime.utcnow()
            }
        )
        db.session.commit()
    except Exception as e:
        logger.error(f"Error logging generation history: {str(e)}")
        db.session.rollback()

@generation_bp.route('/story/generate', methods=['GET'])
def generate():
    if 'story_data' not in session:
        return redirect(url_for('index'))
    return render_template('story/generate.html', story=session['story_data'])

import os # Make sure os is imported

@generation_bp.route('/story/regenerate_image', methods=['POST'])
def regenerate_image():
    try:
        # Fetch API key and instantiate ImageGenerator inside route
        api_key = os.getenv('GEMINI_API_KEY')
        logger.info(f"Regenerate Image: Retrieved GEMINI_API_KEY: {'*****' if api_key else 'None'}") # Log the key presence
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment for regenerate_image.")
            return jsonify({'error': 'Image generation service not configured.'}), 500
        image_service = ImageGenerator(api_key=api_key)

        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
            
        text = data['text']
        index = data.get('index')
        style = data.get('style', 'realistic') # Style is likely not used by current Gemini model call

        # Generate chain of image prompts using Gemini
        story_context = session.get('story_data', {}).get('story_context', '')
        image_prompts = prompt_generator.generate_image_prompt(story_context, text, use_chain=True)

        # Generate new image with chained prompts (removed style argument)
        result = image_service.generate_image_chain(image_prompts)
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

@generation_bp.route('/story/generate_audio', methods=['POST'])
def generate_audio():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
            
        text = data['text']
        index = data.get('index')
        is_retry = data.get('is_retry', False)
        
        # Get temp_id from session
        story_data = session.get('story_data', {})
        temp_id = story_data.get('temp_id')
        
        if not temp_id:
            return jsonify({'error': 'No story session found'}), 404
        
        # Generate audio with retry information
        try:
            audio_url = audio_service.generate_audio(text)
            if not audio_url:
                error_message = "Failed to generate audio"
                if is_retry:
                    error_message += ". Please try again later or contact support if the issue persists."
                
                # Log failed attempt
                log_generation_history(
                    temp_id=temp_id,
                    index=index,
                    generation_type='audio',
                    status='failed',
                    error_message=error_message
                )
                return jsonify({'error': error_message}), 500
                
        except Exception as audio_error:
            logger.error(f"Audio generation error: {str(audio_error)}")
            error_message = str(audio_error)
            
            # Log failed audio generation attempt
            log_generation_history(
                temp_id=temp_id,
                index=index,
                generation_type='audio',
                status='failed',
                error_message=error_message
            )
            
            if is_retry:
                error_message += ". Please try again later or contact support if the issue persists."
            return jsonify({'error': error_message}), 500
            
        # Update temp data storage
        if index is not None:
            temp_data = TempBookData.query.get(temp_id)
            if temp_data:
                book_data = temp_data.data
                if index < len(book_data['paragraphs']):
                    book_data['paragraphs'][index]['audio_url'] = audio_url
                    temp_data.data = book_data
                    
                    # Log successful audio generation
                    log_generation_history(
                        temp_id=temp_id,
                        index=index,
                        generation_type='audio',
                        status='success',
                        result_url=audio_url
                    )
                    
                    try:
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Error updating temp data: {str(e)}")
                        return jsonify({'error': 'Failed to save generated audio'}), 500
            
        return jsonify({
            'success': True,
            'audio_url': audio_url
        })
        
    except Exception as e:
        logger.error(f"Error in generate_audio route: {str(e)}")
        
        # Log unexpected error
        if temp_id:
            log_generation_history(
                temp_id=temp_id,
                index=index,
                generation_type='audio',
                status='failed',
                error_message=str(e)
            )
            
        error_message = str(e)
        if is_retry:
            error_message += ". Please try again later or contact support if the issue persists."
        return jsonify({'error': error_message}), 500

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

@generation_bp.route('/story/generate_image', methods=['POST'])
def generate_image():
    temp_id = None # Initialize temp_id to prevent UnboundLocalError
    try:
        # Fetch API key and instantiate ImageGenerator inside route
        api_key = os.getenv('GEMINI_API_KEY')
        logger.info(f"Generate Image: Retrieved GEMINI_API_KEY: {'*****' if api_key else 'None'}") # Log the key presence
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment for generate_image.")
            return jsonify({'error': 'Image generation service not configured.'}), 500
        image_service = ImageGenerator(api_key=api_key)

        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
            
        text = data['text']
        index = data.get('index')
        style = data.get('style', 'realistic') # Style is likely not used by current Gemini model call
        is_retry = data.get('is_retry', False)
        story_context = data.get('story_context', '')

        # Generate chain of image prompts
        image_prompts = prompt_generator.generate_image_prompt(story_context, text, use_chain=True)

        # Generate new image (style argument already removed in previous steps, ensuring consistency)
        result = image_service.generate_image_chain(image_prompts)

        if not result:
            error_message = "Failed to generate image"
            if is_retry:
                error_message += ". Please try again later."
            return jsonify({'error': error_message}), 500

        # Get temp_id from session if available
        story_data = session.get('story_data', {})
        temp_id = story_data.get('temp_id')
        
        # Removed duplicated block that re-generated prompts and called generate_image_chain again
        
        # This block handles the result from the single call above
        if not result:
            error_message = "Failed to generate image after multiple attempts"
            if is_retry:
                error_message += ". Please try again later or contact support if the issue persists."
            
            # Log failed attempt
            log_generation_history(
                temp_id=temp_id,
                index=index,
                generation_type='image',
                status='failed',
                error_message=error_message,
                prompt=str(image_prompts),
                retries=0
            )
            return jsonify({'error': error_message}), 500
            
        # If result contains error information
        if 'error' in result and result.get('status') == 'failed':
            error_message = result['error']
            if is_retry:
                error_message += f" (Retry attempt failed after {result.get('retries', 0)} attempts)"
            
            # Log failed attempt with retries
            log_generation_history(
                temp_id=temp_id,
                index=index,
                generation_type='image',
                status='failed',
                error_message=error_message,
                prompt=str(image_prompts),
                retries=result.get('retries', 0)
            )
            return jsonify({'error': error_message}), 500
            
        # Update temp data storage
        if index is not None:
            temp_data = TempBookData.query.get(temp_id)
            if temp_data:
                book_data = temp_data.data
                if index < len(book_data['paragraphs']):
                    book_data['paragraphs'][index]['image_url'] = result['url']
                    book_data['paragraphs'][index]['image_prompt'] = result['prompt']
                    temp_data.data = book_data
                    
                    # Log successful generation
                    log_generation_history(
                        temp_id=temp_id,
                        index=index,
                        generation_type='image',
                        status='success',
                        prompt=result['prompt'],
                        result_url=result['url'],
                        retries=result.get('retries', 0)
                    )
                    
                    try:
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Error updating temp data: {str(e)}")
                        return jsonify({'error': 'Failed to save generated image'}), 500
            
        return jsonify({
            'success': True,
            'image_url': result['url'],
            'image_prompt': result['prompt']
        })
        
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        
        # Log unexpected error
        if temp_id:
            log_generation_history(
                temp_id=temp_id,
                index=index,
                generation_type='image',
                status='failed',
                error_message=str(e)
            )
            
        error_message = str(e)
        if is_retry:
            error_message += ". Please try again later or contact support if the issue persists."
        return jsonify({'error': error_message}), 500
