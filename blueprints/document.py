from flask import Blueprint, request, jsonify, session, Response, stream_with_context
from werkzeug.utils import secure_filename
import os
import json
from pathlib import Path
from services.document_processor import DocumentProcessor

doc_bp = Blueprint('document', __name__)
doc_processor = DocumentProcessor()

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
                processor = DocumentProcessor()
                for progress in processor.process_document(str(file_path)):
                    # Convert ProcessingProgress to dict
                    progress_dict = {
                        'status': progress.stage.value,
                        'message': progress.message,
                        'progress': float(progress.progress)
                    }
                    
                    if progress.stage.value == 'complete' and progress.details:
                        session['story_data'] = {
                            'paragraphs': [{
                                'text': str(p['text']),
                                'image_url': None,
                                'audio_url': None
                            } for p in progress.details['paragraphs']]
                        }
                        progress_dict['redirect'] = '/story/edit'
                    
                    # Ensure proper JSON encoding
                    response = f"data: {json.dumps(progress_dict, ensure_ascii=False, separators=(',', ':'))}\\n\\n"
                    yield response

            except Exception as e:
                error_dict = {'status': 'error', 'message': str(e)}
                yield f"data: {json.dumps(error_dict, ensure_ascii=False)}\\n\\n"
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream'
        )
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': str(e)}), 500
