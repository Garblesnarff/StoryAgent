from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, flash
from services.text_generator import TextGenerator
from services.image_generator import ImageGenerator
from services.hume_audio_generator import HumeAudioGenerator
from services.regeneration_service import RegenerationService
import logging

# Configure logging
logger = logging.getLogger(__name__)

story_bp = Blueprint('story', __name__)
text_service = TextGenerator()
image_service = ImageGenerator()
audio_service = HumeAudioGenerator()
regeneration_service = RegenerationService(image_service, audio_service)

@story_bp.route('/story/edit', methods=['GET'])
def edit():
    story_data = session.get('story_data')
    if not story_data or 'paragraphs' not in story_data:
        logger.warning('No valid story data found in session')
        flash('Please generate a story first')
        return redirect(url_for('index'))
    
    # Add debug logging
    logger.info(f'Story data found in session: {len(story_data["paragraphs"])} paragraphs')
    return render_template('story/edit.html', story=story_data)

@story_bp.route('/story/update_paragraph', methods=['POST'])
def update_paragraph():
    try:
        # Check if story data exists in session
        if 'story_data' not in session:
            logger.error('No story data found in session during paragraph update')
            return jsonify({'error': 'No story data found'}), 404

        data = request.get_json()
        if not data:
            logger.error('No JSON data received in request')
            return jsonify({'error': 'No data provided'}), 400

        text = data.get('text')
        index = data.get('index')
        
        if text is None or index is None:
            logger.error(f'Invalid update data - text: {bool(text)}, index: {index}')
            return jsonify({'error': 'Invalid data provided'}), 400
            
        # Update story in session
        story_data = session['story_data']
        if not isinstance(story_data, dict) or 'paragraphs' not in story_data:
            logger.error('Invalid story data structure in session')
            return jsonify({'error': 'Invalid story data structure'}), 500
            
        if index >= len(story_data['paragraphs']):
            logger.error(f'Invalid paragraph index: {index}')
            return jsonify({'error': 'Invalid paragraph index'}), 400
            
        story_data['paragraphs'][index]['text'] = text
        session['story_data'] = story_data
        session.modified = True  # Ensure session is saved
        
        logger.info(f'Successfully updated paragraph {index}')
        return jsonify({
            'success': True,
            'text': text
        })
        
    except Exception as e:
        logger.error(f'Error updating paragraph: {str(e)}')
        return jsonify({'error': str(e)}), 500
