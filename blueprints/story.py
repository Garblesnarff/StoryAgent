from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
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
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

story_bp = Blueprint('story', __name__)
text_service = TextGenerator()
image_service = ImageGenerator()
audio_service = HumeAudioGenerator()
book_processor = BookProcessor()
regeneration_service = RegenerationService(image_service, audio_service)

ALLOWED_EXTENSIONS = {'pdf', 'epub', 'html'}
UPLOAD_FOLDER = 'uploads'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_sample_story():
    """Initialize sample story data for testing"""
    return {
        'prompt': 'Sample story for customization',
        'genre': 'fantasy',
        'mood': 'happy',
        'target_audience': 'young_adult',
        'created_at': str(datetime.now()),
        'paragraphs': [
            {
                'text': 'In a mystical realm where dreams take flight, a young wizard discovered an ancient scroll that would change everything.',
                'image_style': 'fantasy',
                'voice_style': 'dramatic',
                'image_url': None
            },
            {
                'text': 'The scroll contained secrets of a forgotten magic, powerful enough to reshape reality itself.',
                'image_style': 'artistic',
                'voice_style': 'mysterious',
                'image_url': None
            }
        ]
    }

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
    try:
        if 'story_data' not in session:
            session['story_data'] = init_sample_story()
            
        # Get full data from temp storage
        temp_id = session['story_data'].get('temp_id')
        if temp_id:
            temp_data = TempBookData.query.get(temp_id)
            if temp_data:
                return render_template('story/edit.html', story=temp_data.data)
        
        return render_template('story/edit.html', story=session['story_data'])
        
    except Exception as e:
        logger.error(f"Error in edit route: {str(e)}")
        return redirect(url_for('index'))

@story_bp.route('/story/customize', methods=['GET'])
def customize_story():
    try:
        # Initialize story data if not present
        if 'story_data' not in session:
            session['story_data'] = init_sample_story()
            logger.info("Initialized sample story data")
        
        story_data = session['story_data']
        
        # Get data from temp storage if available
        temp_id = story_data.get('temp_id')
        if temp_id:
            temp_data = TempBookData.query.get(temp_id)
            if temp_data and temp_data.data:
                story_data = temp_data.data
                logger.info(f"Retrieved story data from temp storage: {temp_id}")
        
        # Validate and ensure required fields
        if not isinstance(story_data, dict):
            story_data = init_sample_story()
            
        if 'paragraphs' not in story_data or not isinstance(story_data['paragraphs'], list):
            story_data['paragraphs'] = init_sample_story()['paragraphs']
        
        # Ensure each paragraph has required fields
        for paragraph in story_data['paragraphs']:
            if not isinstance(paragraph, dict):
                continue
            paragraph.setdefault('image_style', 'realistic')
            paragraph.setdefault('voice_style', 'neutral')
            paragraph.setdefault('text', paragraph.get('text', 'Sample paragraph text'))
        
        # Update session
        session['story_data'] = story_data
        logger.info(f"Rendering customize page with {len(story_data['paragraphs'])} paragraphs")
        
        return render_template('story/customize.html', story=story_data)
    
    except Exception as e:
        logger.error(f"Error in customize route: {str(e)}")
        return render_template('story/customize.html', story=init_sample_story())

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
        if temp_id:
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
        else:
            # Update in session
            story_data = session['story_data']
            if index >= len(story_data['paragraphs']):
                return jsonify({'error': 'Invalid paragraph index'}), 400
                
            story_data['paragraphs'][index]['text'] = text
            session['story_data'] = story_data
            session.modified = True
        
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
            session['story_data'] = init_sample_story()
            
        data = request.get_json()
        if not data or not isinstance(data.get('paragraphs'), list):
            return jsonify({'error': 'Invalid style data format'}), 400

        story_data = session['story_data']
        if not isinstance(story_data, dict):
            story_data = init_sample_story()
            
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