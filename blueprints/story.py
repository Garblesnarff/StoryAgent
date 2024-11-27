"""
Story Blueprint Module

This module handles all story-related operations including:
- Story editing and customization
- File upload and processing
- Media generation and regeneration
- Session management and data persistence

The blueprint provides routes for:
1. Story editing interface
2. File upload handling
3. Style customization
4. Paragraph updates
5. Media regeneration

Dependencies:
- Flask for web framework
- SQLAlchemy for database operations
- Various service modules for content generation
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, flash
from services.text_generator import TextGenerator
from services.image_generator import ImageGenerator
from services.hume_audio_generator import HumeAudioGenerator
from services.book_processor import BookProcessor
from services.regeneration_service import RegenerationService
from database import db
import os
from werkzeug.utils import secure_filename
from models import TempBookData, StyleCustomization
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize blueprint and services
story_bp = Blueprint('story', __name__)
text_service = TextGenerator()
image_service = ImageGenerator()
audio_service = HumeAudioGenerator()
book_processor = BookProcessor()
regeneration_service = RegenerationService(image_service, audio_service)

# File handling configuration
ALLOWED_EXTENSIONS = {'pdf', 'epub', 'html'}
UPLOAD_FOLDER = 'uploads'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@story_bp.route('/story/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        try:
            # Process the file using BookProcessor service
            result = book_processor.process_file(file)
            
            # Store necessary data in session
            session['story_data'] = {
                'temp_id': result['temp_id'],
                'source_file': result['source_file'],
                'paragraphs': result.get('paragraphs', [])
            }
            
            return jsonify({
                'status': 'complete',
                'message': 'Processing complete',
                'progress': 100,
                'redirect': '/story/edit'
            })
            
        except Exception as e:
            logger.error(f"Error processing upload: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    return jsonify({'error': 'Invalid file type'}), 400

@story_bp.route('/story/edit', methods=['GET'])
def edit():
    """
    Render the story editing interface with the current story data.
    
    This route handles the story editing interface by:
    1. Validating session data exists and is properly structured
    2. Retrieving and validating story data from temporary storage
    3. Processing and preparing data for the React NodeEditor component
    4. Handling various error cases with appropriate user feedback
    
    Returns:
        Rendered template with story data or redirect response
        
    Data Flow:
        1. Session validation -> temp storage retrieval -> data validation -> template rendering
        2. Error states are logged and handled at each step
        
    Story Data Structure:
        {
            'temp_id': str,           # Unique identifier for temporary storage
            'paragraphs': List[Dict],  # List of paragraph objects with text and media URLs
            'metadata': Dict,          # Optional metadata about the story
            'created_at': str,         # Timestamp of creation
            'modified_at': str         # Timestamp of last modification
        }
    """
    try:
        # Step 1: Validate session data
        if 'story_data' not in session:
            logger.warning("No story data in session, redirecting to index")
            flash('Please start by creating a new story', 'warning')
            return redirect(url_for('index'))
        
        session_data = session['story_data']
        logger.info(f"Processing story edit request with session data: {session_data.keys()}")
            
        # Step 2: Validate and retrieve temp_id
        temp_id = session_data.get('temp_id')
        if not temp_id:
            logger.error("Missing temp_id in session data")
            flash('Invalid story data. Please create a new story.', 'error')
            return redirect(url_for('index'))
            
        # Step 3: Retrieve and validate temporary storage data
        temp_data = TempBookData.query.get(temp_id)
        if not temp_data:
            logger.error(f"No temporary data found for ID: {temp_id}")
            flash('Story data not found. Please create a new story.', 'error')
            return redirect(url_for('index'))
            
        # Step 4: Validate story data structure
        story_data = temp_data.data
        if not isinstance(story_data, dict) or 'paragraphs' not in story_data:
            logger.error(f"Invalid story data structure for ID: {temp_id}")
            flash('Invalid story format. Please create a new story.', 'error')
            return redirect(url_for('index'))
            
        # Step 5: Ensure all paragraphs have required fields
        for i, paragraph in enumerate(story_data['paragraphs']):
            if 'text' not in paragraph:
                logger.error(f"Missing text in paragraph {i}")
                flash('Invalid paragraph data. Please create a new story.', 'error')
                return redirect(url_for('index'))
                
        logger.info(f"Successfully prepared story data with {len(story_data['paragraphs'])} paragraphs")
            
        # Step 6: Render template with validated story data
        return render_template('story/edit.html', 
                            story=story_data,
                            error_handling=True)
        
    except Exception as e:
        logger.error(f"Error in edit route: {str(e)}", exc_info=True)
        flash('An error occurred while loading the story editor', 'error')
        return redirect(url_for('index'))

@story_bp.route('/story/customize', methods=['GET'])
def customize_story():
    try:
        # Check if story data exists in session
        if 'story_data' not in session:
            logger.warning("No story data in session, redirecting to home with flash message")
            flash('Please generate a story first before customizing', 'warning')
            return redirect(url_for('index'))

        story_data = session['story_data']
        
        # Validate story data structure
        if not isinstance(story_data, dict) or 'paragraphs' not in story_data:
            logger.error("Invalid story data structure")
            flash('Invalid story data. Please generate a new story.', 'error')
            return redirect(url_for('index'))

        # Get data from temp storage if available
        temp_id = story_data.get('temp_id')
        if temp_id:
            temp_data = TempBookData.query.get(temp_id)
            if temp_data:
                story_data = temp_data.data

        # Ensure paragraphs exist and are properly formatted
        if not story_data.get('paragraphs'):
            logger.error("No paragraphs found in story data")
            flash('No story content found. Please generate a new story.', 'error')
            return redirect(url_for('index'))

        # Initialize default styles if not present
        for paragraph in story_data['paragraphs']:
            if 'image_style' not in paragraph:
                paragraph['image_style'] = 'realistic'

        # Update session with initialized data
        session['story_data'] = story_data
        session.modified = True

        return render_template('story/customize.html', story=story_data)

    except Exception as e:
        logger.error(f"Error in customize route: {str(e)}")
        flash('An error occurred while loading the customization page.', 'error')
        return redirect(url_for('index'))

@story_bp.route('/story/update_paragraph', methods=['POST'])
def update_paragraph():
    try:
        if 'story_data' not in session:
            return jsonify({'error': 'No story data found'}), 404

        data = request.get_json()
        text = data.get('text')
        index = data.get('index')
        
        if not text or index is None:
            return jsonify({'error': 'Invalid data provided'}), 400
        
        # Get data from temp storage
        temp_id = session['story_data'].get('temp_id')
        if not temp_id:
            return jsonify({'error': 'No temp data found'}), 404
            
        temp_data = TempBookData.query.get(temp_id)
        if not temp_data:
            return jsonify({'error': 'Temp data not found'}), 404
            
        # Update paragraph
        story_data = temp_data.data
        if index >= len(story_data['paragraphs']):
            return jsonify({'error': 'Invalid paragraph index'}), 400
            
        story_data['paragraphs'][index]['text'] = text
        temp_data.data = story_data
        db.session.commit()
        
        # Generate new media if requested
        if data.get('generate_media', False):
            try:
                image_url = image_service.generate_image(text)
                audio_url = audio_service.generate_audio(text)
                
                # Update media URLs in temp data
                story_data['paragraphs'][index]['image_url'] = image_url
                story_data['paragraphs'][index]['audio_url'] = audio_url
                temp_data.data = story_data
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'text': text,
                    'image_url': image_url,
                    'audio_url': audio_url
                })
            except Exception as media_error:
                logger.error(f"Error generating media: {str(media_error)}")
                return jsonify({
                    'success': True,
                    'text': text,
                    'error': 'Failed to generate media'
                })
        
        return jsonify({
            'success': True,
            'text': text
        })
        
    except Exception as e:
        logger.error(f"Error updating paragraph: {str(e)}")
        return jsonify({'error': str(e)}), 500

@story_bp.route('/story/update_style', methods=['POST'])
def update_style():
    try:
        if 'story_data' not in session:
            return jsonify({'error': 'No story data found'}), 404
            
        data = request.get_json()
        if not data or not isinstance(data.get('paragraphs'), list):
            return jsonify({'error': 'Invalid style data format'}), 400

        story_data = session['story_data']
        if not isinstance(story_data, dict):
            return jsonify({'error': 'Invalid story data in session'}), 500
            
        # Ensure paragraphs exist
        if 'paragraphs' not in story_data:
            story_data['paragraphs'] = []
            
        # Update styles with proper error checking
        for paragraph_style in data['paragraphs']:
            if not isinstance(paragraph_style, dict):
                continue
                
            index = paragraph_style.get('index')
            if index is None or not isinstance(index, int):
                continue
                
            # Extend paragraphs array if needed
            while len(story_data['paragraphs']) <= index:
                story_data['paragraphs'].append({})
                
            # Update style properties
            story_data['paragraphs'][index].update({
                'image_style': paragraph_style.get('image_style', 'realistic'),
                'voice_style': paragraph_style.get('voice_style', 'neutral')
            })
        
        # Store updated data in session
        session['story_data'] = story_data
        session.modified = True
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error updating style: {str(e)}")
        return jsonify({'error': str(e)}), 500