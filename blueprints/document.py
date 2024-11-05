from flask import Blueprint, request, jsonify, session, send_file, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
from services.document_processor import DocumentProcessor
from services.image_generator import ImageGenerator
from services.hume_audio_generator import HumeAudioGenerator
import json
from flask import Response, stream_with_context

doc_bp = Blueprint('doc', __name__)
doc_processor = DocumentProcessor()
image_generator = ImageGenerator()
audio_generator = HumeAudioGenerator()

ALLOWED_EXTENSIONS = {'pdf', 'epub', 'html'}
UPLOAD_FOLDER = 'uploads'

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@doc_bp.route('/doc/upload', methods=['GET', 'POST'])
def upload_document():
    if request.method == 'GET':
        return render_template('document/upload.html')
        
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
        
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Process document
        file_type = filename.rsplit('.', 1)[1].lower()
        result = doc_processor.process_document(file_path, file_type)
        
        # Transform into session format
        paragraphs = []
        for chapter in result['chapters']:
            for para in chapter['paragraphs']:
                paragraphs.append({
                    'text': para['text'],
                    'chapter': chapter['number'],
                    'chapter_title': chapter['title'],
                    'image_prompt': para['suggested_image_prompt'],
                    'image_url': None,
                    'audio_url': None
                })
        
        # Store in session
        session['book_data'] = {
            'type': 'processed_book',
            'filename': filename,
            'metadata': result['metadata'],
            'paragraphs': paragraphs
        }
        
        # Clean up uploaded file
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed {len(paragraphs)} paragraphs',
            'metadata': result['metadata'],
            'redirect': '/doc/view'
        })
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': str(e)}), 500

@doc_bp.route('/doc/view')
def view_document():
    if 'book_data' not in session:
        return redirect(url_for('doc.upload_document'))
    return render_template('document/view.html', book=session['book_data'])

@doc_bp.route('/doc/batch', methods=['POST'])
def generate_batch():
    """Generate media for a batch of paragraphs"""
    if 'book_data' not in session:
        return jsonify({'error': 'No book data found'}), 404
        
    data = request.get_json()
    start_index = data.get('start_index', 0)
    batch_size = data.get('batch_size', 5)
    
    book_data = session['book_data']
    
    def generate():
        try:
            batch = book_data['paragraphs'][start_index:start_index + batch_size]
            
            for i, paragraph in enumerate(batch):
                current_index = start_index + i
                
                # Generate image
                yield json.dumps({
                    'status': 'generating_image',
                    'index': current_index,
                    'message': f'Generating image {i+1}/{len(batch)}'
                }) + '\n'
                
                image_url = image_generator.generate_image(paragraph['image_prompt'])
                paragraph['image_url'] = image_url
                
                # Generate audio
                yield json.dumps({
                    'status': 'generating_audio',
                    'index': current_index,
                    'message': f'Generating audio {i+1}/{len(batch)}'
                }) + '\n'
                
                audio_url = audio_generator.generate_audio(paragraph['text'])
                paragraph['audio_url'] = audio_url
                
                # Send complete paragraph update
                yield json.dumps({
                    'status': 'paragraph_complete',
                    'index': current_index,
                    'data': paragraph
                }) + '\n'
                
                # Update session after each paragraph
                book_data['paragraphs'][current_index] = paragraph
                session['book_data'] = book_data
                
            yield json.dumps({
                'status': 'batch_complete',
                'message': f'Completed batch of {len(batch)} paragraphs'
            }) + '\n'
            
        except Exception as e:
            yield json.dumps({
                'status': 'error',
                'message': str(e)
            }) + '\n'
            
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@doc_bp.route('/doc/enhance', methods=['POST'])
def enhance_paragraph():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
            
        result = doc_processor.enhance_paragraph_prompts(data['text'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
