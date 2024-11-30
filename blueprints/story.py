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

from functools import wraps
from typing import Callable, Any
from flask import session, redirect, url_for, flash

def require_story_data(f: Callable) -> Callable:
    """
    Decorator to validate story data presence in session.
    Ensures routes have access to required story data before processing.
    
    Args:
        f: The route function to wrap
        
    Returns:
        Wrapped function that validates session data
        
    Redirects:
        To index page with warning if story data is missing
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if 'story_data' not in session:
            logger.warning("No story data in session, redirecting to index")
            flash('Please start by creating a new story', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def validate_temp_data(temp_id: str) -> Optional[TempBookData]:
    """
    Validates and retrieves temporary book data.
    
    Args:
        temp_id: Temporary storage identifier
        
    Returns:
        TempBookData if found and valid, None otherwise
        
    Raises:
        ValueError: If temp_id is invalid or data is corrupted
    """
    if not temp_id:
        raise ValueError("Missing temp_id")
        
    temp_data = TempBookData.query.get(temp_id)
    if not temp_data:
        raise ValueError(f"No temporary data found for ID: {temp_id}")
        
    if not isinstance(temp_data.data, dict) or 'paragraphs' not in temp_data.data:
        raise ValueError(f"Invalid story data structure for ID: {temp_id}")
        
    return temp_data
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
    """
    Handle book file upload and processing.

    Accepts multipart/form-data POST request with a file field.
    Processes supported file types (PDF, EPUB, HTML) and prepares
    them for story generation.

    Request:
        - file: File object (required)
            Supported formats: PDF, EPUB, HTML
            Max size: Determined by Flask config

    Returns:
        JSON Response:
        - Success (200):
            {
                'status': 'complete',
                'message': 'Processing complete',
                'progress': 100,
                'redirect': '/story/edit'
            }
        
        - Error (400):
            {'error': 'Error message'} for client errors:
            - No file provided
            - Empty filename
            - Invalid file type
            
        - Error (500):
            {'error': 'Error message'} for server processing errors

    Session:
        Stores processed data under 'story_data' key:
        - temp_id: Unique identifier for temporary storage
        - source_file: Original filename
        - paragraphs: Extracted text content
    """
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
@require_story_data
def edit():
    """
    Render the story editing interface with the current story data.

    This endpoint provides the main story editing interface, combining text content,
    generated media, and customization options. It performs extensive validation
    to ensure data integrity and proper state management.

    Returns:
        Success:
            Rendered template 'story/edit.html' with formatted story data
        Error:
            Redirect to index with appropriate error message

    Session Requirements:
        - story_data: {
            temp_id: str,              # Temporary storage ID
            source_file: str,          # Original file name
            paragraphs: List[dict]     # Story content
        }
    """
    try:
        session_data = session['story_data']
        logger.info(f"Processing story edit request with session data: {session_data.keys()}")
            
        # Validate and retrieve temp data
        temp_data = validate_temp_data(session_data.get('temp_id'))
        story_data = temp_data.data
            
        logger.info(f"Successfully prepared story data with {len(story_data['paragraphs'])} paragraphs")
            
        # Transform data for the node editor
        formatted_story = {
            'paragraphs': [{
                'text': p.get('text', ''),
                'image_url': p.get('image_url'),
                'image_prompt': p.get('image_prompt'),
                'audio_url': p.get('audio_url'),
                'style': p.get('style', 'realistic'),
                'index': idx
            } for idx, p in enumerate(story_data.get('paragraphs', []))],
            'metadata': story_data.get('metadata', {}),
            'created_at': story_data.get('created_at'),
            'modified_at': story_data.get('modified_at')
        }
        
        return render_template('story/edit.html', 
                            story=formatted_story,
                            error_handling=True)
        
    except ValueError as e:
        logger.error(f"Validation error in edit route: {str(e)}")
        flash(str(e), 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in edit route: {str(e)}", exc_info=True)
        flash('An error occurred while loading the story editor', 'error')
        return redirect(url_for('index'))

@story_bp.route('/story/customize', methods=['GET'])
@require_story_data
def customize_story():
    """
    Customize story visualization styles and parameters.
    
    Provides interface for customizing image and audio generation
    parameters for each paragraph. Initializes default styles
    if not already present.
    
    Returns:
        Success: Rendered customize.html template with story data
        Error: Redirect to index with error message
    """
    try:
        story_data = session['story_data']
        
        # Get data from temp storage if available
        temp_id = story_data.get('temp_id')
        if temp_id:
            temp_data = validate_temp_data(temp_id)
            story_data = temp_data.data

        # Initialize default styles if not present
        for paragraph in story_data['paragraphs']:
            if 'image_style' not in paragraph:
                paragraph['image_style'] = 'realistic'

        # Update session with initialized data
        session['story_data'] = story_data
        session.modified = True

        return render_template('story/customize.html', story=story_data)

    except ValueError as e:
        logger.error(f"Validation error in customize route: {str(e)}")
        flash(str(e), 'error')
        return redirect(url_for('index'))
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