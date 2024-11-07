from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from services.text_generator import TextGenerator
from services.image_generator import ImageGenerator
from services.hume_audio_generator import HumeAudioGenerator
from services.book_processor import BookProcessor
from database import db
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from models import TempBookData
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

story_bp = Blueprint('story', __name__)
text_service = TextGenerator()
image_service = ImageGenerator()
audio_service = HumeAudioGenerator()
book_processor = BookProcessor()

ALLOWED_EXTENSIONS = {'pdf', 'epub', 'html'}
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@story_bp.route('/story/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                
                logger.info(f"Processing file: {filename}")
                
                # Process file based on type
                ext = filename.rsplit('.', 1)[1].lower()
                if ext == 'pdf':
                    paragraphs = book_processor.process_pdf(file_path)
                elif ext == 'epub':
                    paragraphs = book_processor.process_epub(file_path)
                else:  # html
                    paragraphs = book_processor.process_html(file_path)
                    
                if not paragraphs:
                    raise Exception("No valid content extracted from file")
                    
                # Store data in temp table
                temp_id = str(uuid.uuid4())
                temp_data = TempBookData(
                    id=temp_id,
                    data={
                        'source_file': filename,
                        'paragraphs': paragraphs,
                        'created_at': str(datetime.now())
                    }
                )
                db.session.add(temp_data)
                db.session.commit()
                
                # Store minimal data in session
                session['story_data'] = {
                    'temp_id': temp_id,
                    'source_file': filename
                }
                
                logger.info(f"Successfully processed file: {filename}")
                
                # Clean up uploaded file
                os.remove(file_path)
                
                return jsonify({
                    'status': 'complete',
                    'message': 'Processing complete',
                    'progress': 100,
                    'redirect': '/story/edit'
                })
                
            except Exception as e:
                logger.error(f"Error processing file: {str(e)}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                return jsonify({'error': str(e)}), 500
                
        return jsonify({'error': 'Invalid file type'}), 400
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@story_bp.route('/story/edit', methods=['GET'])
def edit():
    if 'story_data' not in session:
        return redirect(url_for('index'))
        
    # Get full data from temp storage
    temp_id = session['story_data'].get('temp_id')
    if temp_id:
        temp_data = TempBookData.query.get(temp_id)
        if temp_data:
            return render_template('story/edit.html', story=temp_data.data)
            
    return redirect(url_for('index'))

@story_bp.route('/story/update_paragraph', methods=['POST'])
def update_paragraph():
    try:
        if 'story_data' not in session:
            return jsonify({'error': 'No story data found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
            
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
        
        return jsonify({
            'success': True,
            'text': text
        })
        
    except Exception as e:
        logger.error(f"Error updating paragraph: {str(e)}")
        return jsonify({'error': str(e)}), 500

@story_bp.route('/story/regenerate_audio', methods=['POST'])
def regenerate_audio():
    try:
        if 'story_data' not in session:
            return jsonify({'error': 'No story data found'}), 404

        data = request.get_json()
        text = data.get('text')
        index = data.get('index')
        
        if not text or index is None:
            return jsonify({'error': 'Invalid data provided'}), 400
            
        # Get data from temp storage if exists
        temp_id = session['story_data'].get('temp_id')
        if temp_id:
            temp_data = TempBookData.query.get(temp_id)
            if not temp_data:
                return jsonify({'error': 'Temp data not found'}), 404
            story_data = temp_data.data
        else:
            story_data = session['story_data']
            
        # Regenerate audio
        audio_url = audio_service.generate_audio(text)
        if not audio_url:
            return jsonify({'error': 'Failed to generate audio'}), 500
            
        # Update storage
        story_data['paragraphs'][index]['audio_url'] = audio_url
        if temp_id and temp_data:
            temp_data.data = story_data
            db.session.commit()
        else:
            session['story_data'] = story_data
            
        return jsonify({
            'success': True,
            'audio_url': audio_url
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@story_bp.route('/story/regenerate_image', methods=['POST'])
def regenerate_image():
    try:
        if 'story_data' not in session:
            return jsonify({'error': 'No story data found'}), 404

        data = request.get_json()
        text = data.get('text')
        index = data.get('index')
        
        if not text or index is None:
            return jsonify({'error': 'Invalid data provided'}), 400
            
        # Get data from temp storage if exists
        temp_id = session['story_data'].get('temp_id')
        if temp_id:
            temp_data = TempBookData.query.get(temp_id)
            if not temp_data:
                return jsonify({'error': 'Temp data not found'}), 404
            story_data = temp_data.data
        else:
            story_data = session['story_data']
            
        # Regenerate image
        image_url = image_service.generate_image(text)
        if not image_url:
            return jsonify({'error': 'Failed to generate image'}), 500
            
        # Update storage
        story_data['paragraphs'][index]['image_url'] = image_url
        if temp_id and temp_data:
            temp_data.data = story_data
            db.session.commit()
        else:
            session['story_data'] = story_data
            
        return jsonify({
            'success': True,
            'image_url': image_url
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@story_bp.route('/story/generate', methods=['GET'])
def generate():
    if 'story_data' not in session:
        return redirect(url_for('index'))
        
    temp_id = session['story_data'].get('temp_id')
    if temp_id:
        temp_data = TempBookData.query.get(temp_id)
        if temp_data:
            return render_template('story/generate.html', story=temp_data.data)
            
    return redirect(url_for('index'))