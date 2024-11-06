from flask import Blueprint, request, jsonify, session, Response, stream_with_context
from werkzeug.utils import secure_filename
import os
import json
import logging
from pathlib import Path
from services.document_processor import DocumentProcessor

doc_bp = Blueprint('document', __name__)
doc_processor = DocumentProcessor()
logger = logging.getLogger(__name__)

# Configure upload settings
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'epub', 'html'}
UPLOAD_FOLDER = Path('uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@doc_bp.route('/upload', methods=['POST'])
def upload_document():
    """Handle document upload and processing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
        
    try:
        filename = secure_filename(file.filename)
        file_path = UPLOAD_FOLDER / filename
        file.save(file_path)

        def generate():
            try:
                for progress in doc_processor.process_document(str(file_path)):
                    try:
                        # Convert ProcessingProgress to dict with sanitization
                        progress_dict = {
                            'status': str(progress.stage.value),
                            'message': str(progress.message),
                            'progress': float(progress.progress)
                        }
                        
                        if progress.stage.value == 'complete' and progress.details:
                            # Sanitize paragraph data
                            session['story_data'] = {
                                'paragraphs': [{
                                    'text': str(p['text'])[:5000],  # Limit paragraph size
                                    'image_url': None,
                                    'audio_url': None
                                } for p in progress.details['paragraphs']]
                            }
                            progress_dict['redirect'] = '/story/edit'
                        
                        # Ensure proper JSON encoding with error handling
                        json_data = json.dumps(progress_dict, ensure_ascii=False, default=str)
                        yield f"data: {json_data}\n\n"

                    except Exception as json_error:
                        logger.error(f"Error encoding progress: {str(json_error)}")
                        error_dict = {
                            'status': 'error',
                            'message': 'Error encoding progress data'
                        }
                        yield f"data: {json.dumps(error_dict)}\n\n"
                        
            except Exception as e:
                error_dict = {'status': 'error', 'message': str(e)}
                yield f"data: {json.dumps(error_dict)}\n\n"
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream'
        )
        
    except Exception as e:
        logger.error(f"Error handling upload: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': str(e)}), 500
