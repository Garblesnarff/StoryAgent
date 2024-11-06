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
                # Process document synchronously
                processor = DocumentProcessor()
                for progress in processor.process_document(str(file_path)):
                    progress_dict = {
                        'status': progress.stage.value,
                        'message': progress.message,
                        'progress': progress.progress
                    }
                    
                    if progress.stage.value == 'complete' and progress.details:
                        # Store processed paragraphs in session
                        session['story_data'] = {
                            'paragraphs': [{
                                'text': p['text'],
                                'image_url': None,
                                'audio_url': None
                            } for p in progress.details['paragraphs']]
                        }
                        progress_dict['redirect'] = '/story/edit'
                        
                    yield f"data: {json.dumps(progress_dict)}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
            finally:
                # Clean up uploaded file
                if os.path.exists(file_path):
                    os.remove(file_path)

        return Response(
            generate(),
            mimetype='text/event-stream'
        )
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': str(e)}), 500
