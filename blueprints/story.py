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
            paragraphs = result.get('paragraphs', [])
            session['story_data'] = {
                'temp_id': result['temp_id'],
                'source_file': result['source_file'],
                'paragraphs': paragraphs,
                'total_pages': (len(paragraphs) + 9) // 10  # Calculate total pages (10 items per page)
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

@story_bp.route('/story/page/<int:page>', methods=['GET'])
def get_page(page):
    try:
        if 'story_data' not in session:
            return jsonify({'error': 'No story data found'}), 404

        temp_id = session['story_data'].get('temp_id')
        if not temp_id:
            return jsonify({'error': 'No temp data found'}), 404

        temp_data = TempBookData.query.get(temp_id)
        if not temp_data:
            return jsonify({'error': 'Temp data not found'}), 404

        page_data = temp_data.get_page(page)
        return jsonify(page_data)

    except Exception as e:
        logger.error(f"Error getting page {page}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@story_bp.route('/story/edit', methods=['GET'])
def edit():
    try:
        if 'story_data' not in session:
            return redirect(url_for('index'))

        # Get full data from temp storage
        temp_id = session['story_data'].get('temp_id')
        if not temp_id:
            logger.error("No temp_id found in session")
            return redirect(url_for('index'))

        temp_data = TempBookData.query.get(temp_id)
        if not temp_data:
            logger.error(f"No temp data found for ID: {temp_id}")
            return redirect(url_for('index'))

        # Get first page of data
        page_data = temp_data.get_page(1)
        return render_template('story/edit.html', story=page_data)

    except Exception as e:
        logger.error(f"Error in edit route: {str(e)}")
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

@story_bp.route('/story/get_chunks/<int:page>', methods=['GET'])
def get_chunks(page):
    try:
        if 'story_data' not in session:
            return jsonify({'error': 'No story data found'}), 404

        temp_id = session.get('story_data', {}).get('temp_id')
        if not temp_id:
            return jsonify({'error': 'No temp data found'}), 404

        temp_data = TempBookData.query.get(temp_id)
        if not temp_data:
            return jsonify({'error': 'No data found'}), 404

        page_data = temp_data.get_page(page)
        if not page_data:
            return jsonify({'error': 'Invalid page number'}), 400

        # Structure the data consistently 
        return jsonify({
            'paragraphs': page_data['chunks'],
            'current_page': page_data['current_page'],
            'total_pages': page_data['total_pages'],
            'total_paragraphs': len(page_data['chunks']),
            'paragraphs_per_page': page_data['chunks_per_page']
        })

    except Exception as e:
        logger.error(f"Error getting chunks for page {page}: {str(e)}")
        return jsonify({'error': 'Failed to load page'}), 500

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