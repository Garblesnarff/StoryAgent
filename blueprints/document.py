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
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'html', 'md', 'css', 'js', 'py', 'xml', 'rtf'}
UPLOAD_FOLDER = Path('uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@doc_bp.route('/upload', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            logger.error("No file provided in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        logger.info(f"Received file upload request: {file.filename}")
        
        # Add session debug logging
        logger.debug(f"Session before upload: {dict(session)}")
        
        if file.filename == '':
            logger.error("Empty filename provided")
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            logger.error(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Invalid file type'}), 400
        
        filename = secure_filename(file.filename)
        file_path = UPLOAD_FOLDER / filename
        logger.info(f"Saving file to: {file_path}")
        file.save(file_path)

        def generate():
            try:
                logger.info("Starting document processing stream")
                for progress in doc_processor.process_document(str(file_path)):
                    try:
                        progress_dict = {
                            'status': str(progress.stage.value),
                            'message': str(progress.message),
                            'progress': float(progress.progress)
                        }
                        
                        if progress.stage.value == 'error':
                            if progress.details and progress.details.get('error_type') == 'copyright':
                                progress_dict['error_type'] = 'copyright'
                                progress_dict['can_summarize'] = progress.details.get('can_summarize', False)
                        
                        if progress.stage.value == 'complete' and progress.details:
                            # Initialize session data
                            if 'story_data' not in session:
                                session['story_data'] = {}
                            
                            # Update session data
                            session['story_data'].update({
                                'source': 'document',
                                'filename': filename,
                                'paragraphs': [{
                                    'text': str(p['text'])[:5000],
                                    'image_url': None,
                                    'audio_url': None
                                } for p in progress.details['paragraphs']]
                            })
                            
                            # Force session persistence
                            session.permanent = True
                            session.modified = True
                            
                            # Log session state
                            logger.info(f"Updated session with {len(session['story_data']['paragraphs'])} paragraphs")
                            logger.debug(f"Session after update: {dict(session)}")
                            
                            progress_dict['redirect'] = '/story/edit'
                        
                        json_data = json.dumps(progress_dict, ensure_ascii=False)
                        logger.debug(f"Sending progress update: {json_data}")
                        yield f"data: {json_data}\n\n"

                    except Exception as json_error:
                        logger.error(f"Error encoding progress: {str(json_error)}", exc_info=True)
                        yield f"data: {json.dumps({'status': 'error', 'message': str(json_error)})}\n\n"
                        
            except Exception as e:
                logger.error(f"Error in processing stream: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
            finally:
                if os.path.exists(file_path):
                    logger.info(f"Cleaning up uploaded file: {file_path}")
                    os.remove(file_path)

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream'
        )
        
    except Exception as e:
        logger.error(f"Error handling upload: {str(e)}", exc_info=True)
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': str(e)}), 500

@doc_bp.route('/summarize', methods=['POST'])
def summarize_document():
    try:
        if 'file' not in request.files:
            logger.error("No file provided for summary")
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        logger.debug(f"Session before summary: {dict(session)}")
        
        filename = secure_filename(file.filename)
        file_path = UPLOAD_FOLDER / filename
        file.save(file_path)
        
        def generate():
            try:
                for progress in doc_processor.summarize_document(str(file_path)):
                    try:
                        progress_dict = {
                            'status': str(progress.stage.value),
                            'message': str(progress.message),
                            'progress': float(progress.progress)
                        }
                        
                        if progress.stage.value == 'complete' and progress.details:
                            # Initialize session data
                            if 'story_data' not in session:
                                session['story_data'] = {}
                                
                            # Update session data    
                            session['story_data'].update({
                                'source': 'document_summary',
                                'filename': filename,
                                'paragraphs': [{
                                    'text': str(p['text'])[:5000],
                                    'image_url': None,
                                    'audio_url': None
                                } for p in progress.details['paragraphs']]
                            })
                            
                            # Force session persistence
                            session.permanent = True
                            session.modified = True
                            
                            logger.info(f"Stored summary with {len(session['story_data']['paragraphs'])} paragraphs")
                            logger.debug(f"Session after summary: {dict(session)}")
                            
                            progress_dict['redirect'] = '/story/edit'
                            
                        yield f"data: {json.dumps(progress_dict, ensure_ascii=False)}\n\n"
                        
                    except Exception as json_error:
                        logger.error(f"Error encoding summary progress: {str(json_error)}")
                        yield f"data: {json.dumps({'status': 'error', 'message': str(json_error)})}\n\n"
                        
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream'
        )
        
    except Exception as e:
        logger.error(f"Error handling summary: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': str(e)}), 500
