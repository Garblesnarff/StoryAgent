from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, current_app, flash
from services.text_generator import TextGenerator
from services.image_generator import ImageGenerator
from services.hume_audio_generator import HumeAudioGenerator
import logging

story_bp = Blueprint('story', __name__)
logger = logging.getLogger(__name__)

text_service = TextGenerator()
image_service = ImageGenerator()
audio_service = HumeAudioGenerator()

@story_bp.route('/story/edit', methods=['GET'])
def edit():
    try:
        logger.debug(f"Session data at edit route: {dict(session)}")
        
        if 'story_data' not in session:
            logger.error("No story data in session")
            flash('No story data found. Please generate or upload a story first.')
            return redirect(url_for('index'))
            
        story_data = session.get('story_data')
        if not story_data or 'paragraphs' not in story_data:
            logger.error(f"Invalid story data: {story_data}")
            flash('Invalid story data. Please try uploading again.')
            return redirect(url_for('index'))
            
        logger.info(f"Rendering edit page with {len(story_data['paragraphs'])} paragraphs")
        
        # Force session persistence
        session.permanent = True
        session.modified = True
        
        return render_template('story/edit.html', story=story_data)
        
    except Exception as e:
        logger.error(f"Error in edit route: {str(e)}", exc_info=True)
        flash('An error occurred. Please try again.')
        return redirect(url_for('index'))

@story_bp.route('/story/update_paragraph', methods=['POST'])
def update_paragraph():
    try:
        logger.debug(f"Session before paragraph update: {dict(session)}")
        
        if 'story_data' not in session:
            logger.error("No story data found in session")
            return jsonify({'error': 'No story data found'}), 404

        data = request.get_json()
        text = data.get('text')
        index = data.get('index')
        
        if not text or index is None:
            logger.error("Invalid data provided for paragraph update")
            return jsonify({'error': 'Invalid data provided'}), 400
            
        # Update story in session
        story_data = session['story_data']
        if index >= len(story_data['paragraphs']):
            logger.error(f"Invalid paragraph index: {index}")
            return jsonify({'error': 'Invalid paragraph index'}), 400
            
        story_data['paragraphs'][index]['text'] = text
        session['story_data'] = story_data
        session.permanent = True
        session.modified = True
        
        logger.info(f"Updated paragraph {index} with new text")
        logger.debug(f"Session after paragraph update: {dict(session)}")
        
        return jsonify({
            'success': True,
            'text': text
        })
        
    except Exception as e:
        logger.error(f"Error updating paragraph: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
