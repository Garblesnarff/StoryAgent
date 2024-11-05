from flask import Blueprint, request, jsonify, session, Response, stream_with_context
from werkzeug.utils import secure_filename
import os
import json
import google.generativeai as genai
import logging
from pathlib import Path
from services.image_generator import ImageGenerator
from services.hume_audio_generator import HumeAudioGenerator

doc_bp = Blueprint('document', __name__)
image_service = ImageGenerator()
audio_service = HumeAudioGenerator()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure upload directory
UPLOAD_FOLDER = Path('uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'rtf', 'md'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

def process_document_chunk(text):
    """Process a chunk of text using Gemini"""
    try:
        # Generate story structure and enhancements
        prompt = f"""Analyze this text and return:
        1. A story breakdown into 3-5 paragraphs
        2. For each paragraph:
            - Suggested image description
            - Audio narration guidance
            
        Return as JSON with format:
        {{
            "paragraphs": [
                {{
                    "text": "paragraph text",
                    "image_prompt": "detailed image generation prompt",
                    "narration_guidance": "voice and tone guidance for audio"
                }}
            ]
        }}
        
        Text to analyze:
        {text}
        """
        
        response = model.generate_content(prompt)
        return json.loads(response.text)
        
    except Exception as e:
        logger.error(f"Error processing text chunk: {str(e)}")
        return None

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
                # Read file content
                with open(file_path, 'r') as f:
                    text = f.read()
                
                yield json.dumps({
                    'status': 'processing',
                    'message': 'Processing document content'
                }) + '\n'
                
                # Process document
                result = process_document_chunk(text)
                if not result:
                    raise Exception("Failed to process document")
                
                # Store processed data in session
                session['story_data'] = {
                    'prompt': filename,  # Use filename as prompt for context
                    'created_at': str(datetime.now()),
                    'paragraphs': result['paragraphs']
                }
                
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
                # Clean up uploaded file
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
