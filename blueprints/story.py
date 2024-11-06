from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from services.text_generator import TextGenerator
from services.image_generator import ImageGenerator
from services.hume_audio_generator import HumeAudioGenerator
from services.book_processor import BookProcessor
from services.regeneration_service import RegenerationService
import os
from werkzeug.utils import secure_filename

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
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            # Process file based on type
            ext = filename.rsplit('.', 1)[1].lower()
            if ext == 'pdf':
                paragraphs = book_processor.process_pdf(file_path)
            elif ext == 'epub':
                paragraphs = book_processor.process_epub(file_path)
            else:  # html
                paragraphs = book_processor.process_html(file_path)
                
            if not paragraphs:
                raise Exception("Failed to process file")
                
            # Store processed paragraphs in session
            session['story_data'] = {
                'source_file': filename,
                'paragraphs': paragraphs
            }
            
            # Clean up uploaded file
            os.remove(file_path)
            
            return jsonify({
                'status': 'complete',
                'message': 'Processing complete',
                'progress': 100,
                'redirect': '/story/edit'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    return jsonify({'error': 'Invalid file type'}), 400

@story_bp.route('/story/edit', methods=['GET'])
def edit():
    # Check if story data exists in session
    if 'story_data' not in session:
        return redirect(url_for('index'))
    return render_template('story/edit.html', story=session['story_data'])

@story_bp.route('/story/update_paragraph', methods=['POST'])
def update_paragraph():
    try:
        # Check if story data exists in session
        if 'story_data' not in session:
            return jsonify({'error': 'No story data found'}), 404

        data = request.get_json()
        text = data.get('text')
        index = data.get('index')
        
        if not text or index is None:
            return jsonify({'error': 'Invalid data provided'}), 400
            
        # Update story in session
        story_data = session['story_data']
        if index >= len(story_data['paragraphs']):
            return jsonify({'error': 'Invalid paragraph index'}), 400
            
        story_data['paragraphs'][index]['text'] = text
        session['story_data'] = story_data
        
        # Generate new image and audio if requested
        if data.get('generate_media', False):
            image_url = image_service.generate_image(text)
            audio_url = audio_service.generate_audio(text)
            
            # Update media URLs in session
            story_data['paragraphs'][index]['image_url'] = image_url
            story_data['paragraphs'][index]['audio_url'] = audio_url
            session['story_data'] = story_data
            
            return jsonify({
                'success': True,
                'text': text,
                'image_url': image_url,
                'audio_url': audio_url
            })
        
        return jsonify({
            'success': True,
            'text': text
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
