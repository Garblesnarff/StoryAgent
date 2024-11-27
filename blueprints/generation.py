"""
Story Generation Blueprint Module

This module handles all story generation related routes and functionality including:
- Story generation with customizable parameters
- Image generation with style customization
- Audio generation for story narration
- Real-time progress streaming
- Media regeneration capabilities

The blueprint uses various services to handle different aspects of content generation
and maintains state through both session storage and temporary database records.
"""

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
from typing import Dict, Union, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

generation_bp = Blueprint('generation', __name__)
text_service = TextGenerator()
image_service = ImageGenerator()
audio_service = HumeAudioGenerator()
prompt_generator = PromptGenerator()

def send_json_message(message_type: str, message_data: Union[str, Dict], step: Optional[str] = None) -> str:
    """
    Format and serialize JSON messages for SSE (Server-Sent Events) streaming.
    
    This helper function ensures consistent message formatting across all
    streaming responses in the generation process.
    
    Args:
        message_type: Type identifier for the message (e.g., 'log', 'error', 'complete')
        message_data: The actual message content or data payload
        step: Optional step identifier for progress tracking
        
    Returns:
        str: Formatted JSON string with newline terminator for SSE
    """
    message = {
        'type': message_type,
        'message' if isinstance(message_data, str) else 'data': message_data
    }
    if step:
        message['step'] = step
    return json.dumps(message).replace('\n', ' ') + '\n'

@generation_bp.route('/story/generate', methods=['GET'])
def generate():
    """
    Render the story generation page with current story data.
    
    This route checks for existing story data in the session and renders
    the generation template. If no story data exists, redirects to the index page.
    
    Returns:
        Response: Rendered template with story data or redirect response
    """
    if 'story_data' not in session:
        logger.info("No story data found in session, redirecting to index")
        return redirect(url_for('index'))
    return render_template('story/generate.html', story=session['story_data'])

@generation_bp.route('/story/regenerate_image', methods=['POST'])
def regenerate_image():
    """
    Regenerate an image for a specific story paragraph.
    
    This endpoint handles image regeneration requests, including:
    1. Generating new image prompts using context-aware chaining
    2. Creating the image using the specified style
    3. Updating both temporary and session storage with new image data
    
    Request JSON parameters:
        text (str): The paragraph text to generate an image for
        index (int, optional): The paragraph index in the story
        style (str, optional): Image style preference (default: 'realistic')
    
    Returns:
        JSON Response: Contains success status, image URL and prompt,
                      or error details if generation fails
    """
    try:
        # Validate request data
        data = request.get_json()
        if not data or 'text' not in data:
            logger.warning("Invalid request: missing text parameter")
            return jsonify({'error': 'No text provided'}), 400
            
        text = data['text']
        index = data.get('index')
        style = data.get('style', 'realistic')
        
        # Get story context and generate image prompts
        story_context = session.get('story_data', {}).get('story_context', '')
        logger.info(f"Generating image prompts for paragraph {index}")
        image_prompts = prompt_generator.generate_image_prompt(
            story_context, text, use_chain=True
        )
        
        # Generate new image
        logger.info(f"Generating image with style: {style}")
        result = image_service.generate_image_chain(image_prompts, style=style)
        if not result:
            logger.error("Image generation failed: no result returned")
            return jsonify({'error': 'Failed to generate image'}), 500
            
        # Update storage based on availability
        if index is not None:
            story_data = session.get('story_data', {})
            temp_id = story_data.get('temp_id')
            
            if temp_id:
                # Update in temporary storage
                temp_data = TempBookData.query.get(temp_id)
                if temp_data:
                    book_data = temp_data.data
                    if index < len(book_data['paragraphs']):
                        book_data['paragraphs'][index].update({
                            'image_url': result['url'],
                            'image_prompt': result['prompt']
                        })
                        temp_data.data = book_data
                        db.session.commit()
                        logger.info(f"Updated image in temp storage for paragraph {index}")
            else:
                # Update in session storage
                if 'paragraphs' in story_data and index < len(story_data['paragraphs']):
                    story_data['paragraphs'][index].update({
                        'image_url': result['url'],
                        'image_prompt': result['prompt']
                    })
                    session['story_data'] = story_data
                    logger.info(f"Updated image in session storage for paragraph {index}")
        
        return jsonify({
            'success': True,
            'image_url': result['url'],
            'image_prompt': result['prompt']
        })
        
    except Exception as e:
        logger.error(f"Error regenerating image: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to regenerate image',
            'details': str(e)
        }), 500

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
            
            # Add style-specific prompt templates
            style = data.get('style', 'realistic')
            if style == 'realistic':
                prompt_prefix = "Create a photorealistic image with natural lighting and detailed textures showing:"
            elif style == 'artistic':
                prompt_prefix = "Create an artistic interpretation with expressive brushstrokes and bold colors showing:"
            elif style == 'fantasy':
                prompt_prefix = "Create a fantastical and magical scene with ethereal lighting and supernatural elements showing:"

            # Generate chain of image prompts using Gemini
            yield send_json_message('log', 'Generating image prompts...', step='prompt')
            image_prompts = prompt_generator.generate_image_prompt(
                story_context, 
                text,
                use_chain=True
            )
            
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
