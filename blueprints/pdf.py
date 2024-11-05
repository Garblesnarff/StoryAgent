from flask import Blueprint, request, jsonify, session, Response, stream_with_context
from werkzeug.utils import secure_filename
import os
import logging
import json
from services.pdf_processor import PDFProcessor
from services.image_generator import ImageGenerator
from services.hume_audio_generator import HumeAudioGenerator

pdf_bp = Blueprint('pdf', __name__)
pdf_processor = PDFProcessor()
image_generator = ImageGenerator()
audio_generator = HumeAudioGenerator()

ALLOWED_EXTENSIONS = {'pdf', 'epub', 'html'}
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@pdf_bp.route('/upload', methods=['POST'])
async def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
        
    try:
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Get file type
        file_type = filename.rsplit('.', 1)[1].lower()
        
        # Process document and get paragraphs
        with open(filepath, 'rb') as f:
            paragraphs = await pdf_processor.process_document(f, file_type)
        
        # Clean up temporary file
        os.remove(filepath)
        
        # Store in session similar to story generation
        session['story_data'] = {
            'type': 'book',
            'filename': filename,
            'format': file_type,
            'paragraphs': [{'text': p, 'image_url': None, 'audio_url': None} for p in paragraphs]
        }
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed {len(paragraphs)} paragraphs from {file_type.upper()} file',
            'redirect': '/story/edit'  # Reuse existing edit page
        })
        
    except Exception as e:
        logging.error(f"Error processing document: {str(e)}")
        # Clean up file if it exists
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500
