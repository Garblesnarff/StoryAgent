from flask import Blueprint, request, jsonify, session, Response, stream_with_context
from werkzeug.utils import secure_filename
import os
import json
import google.generativeai as genai
import logging
from pathlib import Path
from datetime import datetime

doc_bp = Blueprint('document', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure upload directory
UPLOAD_FOLDER = Path('uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'rtf', 'md'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-pro')  # Use pro model for better document handling

@doc_bp.route('/upload', methods=['POST'])
def upload_document():
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
        file.save(str(file_path))
        
        def generate():
            try:
                # Upload file to Gemini
                yield json.dumps({
                    'status': 'uploading',
                    'message': 'Uploading document to process'
                }) + '\n'
                
                # Using Gemini's file upload
                uploaded_file = genai.upload_file(str(file_path))
                
                yield json.dumps({
                    'status': 'processing',
                    'message': 'Processing document content'
                }) + '\n'
                
                # Process with Gemini
                prompt = '''Analyze this document and break it down into story paragraphs. For each paragraph:
                1. Clean and format the text
                2. Suggest an image description
                3. Provide audio narration guidance
                
                Return as JSON with format:
                {
                    "paragraphs": [
                        {
                            "text": "paragraph text",
                            "image_prompt": "detailed image description",
                            "narration_guidance": "voice and tone guidance"
                        }
                    ]
                }'''
                
                # Generate content with error handling
                response = model.generate_content([
                    prompt,
                    uploaded_file
                ])
                
                if not response.text:
                    raise Exception("Empty response from Gemini API")
                    
                try:
                    result = json.loads(response.text)
                except json.JSONDecodeError:
                    # If response is not JSON, try to extract content
                    result = {
                        "paragraphs": [{
                            "text": response.text,
                            "image_prompt": "Generate an illustration for this text",
                            "narration_guidance": "Read in a clear, engaging tone"
                        }]
                    }
                
                # Store in session
                session['story_data'] = {
                    'prompt': filename,
                    'created_at': str(datetime.now()),
                    'paragraphs': [
                        {
                            'text': p['text'],
                            'image_url': None,
                            'audio_url': None,
                            'image_prompt': p['image_prompt'],
                            'narration_guidance': p['narration_guidance']
                        } for p in result['paragraphs']
                    ]
                }
                # Force session save
                session.modified = True
                
                yield json.dumps({
                    'status': 'complete',
                    'message': 'Document processing complete',
                    'redirect': '/story/edit'
                }) + '\n'
                
            except Exception as e:
                logger.error(f"Error processing document: {str(e)}")
                yield json.dumps({
                    'status': 'error',
                    'message': str(e)
                }) + '\n'
                
            finally:
                # Cleanup
                if file_path.exists():
                    file_path.unlink()
                
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream'
        )
        
    except Exception as e:
        logger.error(f"Error handling upload: {str(e)}")
        if file_path.exists():
            file_path.unlink()
        return jsonify({'error': str(e)}), 500
