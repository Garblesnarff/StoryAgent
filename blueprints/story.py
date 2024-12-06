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

@story_bp.route('/story/edit', methods=['GET'])
def edit():
    try:
        if 'story_data' not in session:
            return redirect(url_for('index'))

        temp_id = session['story_data'].get('temp_id')
        if not temp_id:
            logger.error("No temp_id found in session")
            return redirect(url_for('index'))

        temp_data = TempBookData.query.get(temp_id)
        if not temp_data:
            logger.error(f"No temp data found for ID: {temp_id}")
            return redirect(url_for('index'))

        logger.info(f"Retrieved temp data for ID: {temp_id}")

        # Get all sections
        sections = temp_data.data.get('sections', [])
        if not sections:
            logger.error("No sections found in temp data")
            return redirect(url_for('index'))

        # Get first section's chunks
        first_section = sections[0]
        chunks = first_section.get('chunks', [])
        
        if not chunks and first_section.get('text'):
            # Process the section if no chunks exist but text is available
            logger.info("Processing section text into chunks")
            chunks = book_processor.process_section(first_section)
            first_section['chunks'] = chunks
            first_section['processed'] = True
            temp_data.data['sections'][0] = first_section
            db.session.commit()

        # Get current page from query parameters
        page = request.args.get('page', 1, type=int)
        chunks_per_page = 10
        
        # Calculate pagination
        total_chunks = len(chunks)
        start_idx = (page - 1) * chunks_per_page
        end_idx = start_idx + chunks_per_page
        current_chunks = chunks[start_idx:end_idx]
        
        # Create story data structure
        story_data = {
            'temp_id': temp_id,
            'title': first_section.get('title', 'Untitled Story'),
            'paragraphs': current_chunks,
            'total_sections': len(sections),
            'current_page': page,
            'total_pages': (total_chunks + chunks_per_page - 1) // chunks_per_page,
            'has_next': end_idx < total_chunks,
            'has_prev': page > 1
        }

        logger.info(f"Prepared story data with {len(current_chunks)} chunks for page {page}")
        return render_template('story/edit.html', story=story_data)

    except Exception as e:
        logger.error(f"Error in edit route: {str(e)}", exc_info=True)
        return redirect(url_for('index'))

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
                'title': result.get('title', 'Untitled Story')
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

@story_bp.route('/story/update_paragraph', methods=['POST'])
def update_paragraph():
    try:
        if 'story_data' not in session:
            return jsonify({'error': 'No story data found'}), 404

        data = request.get_json()
        text = data.get('text')
        index = data.get('index')
        
        if text is None or index is None:
            return jsonify({'error': 'Invalid data provided'}), 400
        
        # Get data from temp storage
        temp_id = session['story_data'].get('temp_id')
        if not temp_id:
            return jsonify({'error': 'No temp data found'}), 404
            
        temp_data = TempBookData.query.get(temp_id)
        if not temp_data or not temp_data.data.get('sections'):
            return jsonify({'error': 'Temp data not found'}), 404
            
        # Update paragraph in the first section's chunks
        section = temp_data.data['sections'][0]
        chunks = section.get('chunks', [])
        
        if index >= len(chunks):
            return jsonify({'error': 'Invalid paragraph index'}), 400
            
        chunks[index]['text'] = text
        section['chunks'] = chunks
        temp_data.data['sections'][0] = section
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating temp data: {str(e)}")
            return jsonify({'error': 'Failed to save changes'}), 500
        
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
            
        # Get temp data
        temp_id = session['story_data'].get('temp_id')
        temp_data = TempBookData.query.get(temp_id)
        if not temp_data or not temp_data.data.get('sections'):
            return jsonify({'error': 'No temp data found'}), 404
            
        # Update styles in the first section's chunks
        section = temp_data.data['sections'][0]
        chunks = section.get('chunks', [])
        
        # Update styles with proper error checking
        for paragraph_style in data['paragraphs']:
            if not isinstance(paragraph_style, dict):
                continue
                
            index = paragraph_style.get('index')
            if index is None or not isinstance(index, int) or index >= len(chunks):
                continue
                
            # Update style properties
            chunks[index].update({
                'image_style': paragraph_style.get('image_style', 'realistic'),
                'voice_style': paragraph_style.get('voice_style', 'neutral')
            })
        
        # Save updated chunks
        section['chunks'] = chunks
        temp_data.data['sections'][0] = section
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating styles: {str(e)}")
            return jsonify({'error': 'Failed to save style changes'}), 500
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error updating style: {str(e)}")
        return jsonify({'error': str(e)}), 500

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