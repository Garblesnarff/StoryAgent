from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
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
        
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
            
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        try:
            # Process document
            file_type = filename.rsplit('.', 1)[1].lower()
            result = doc_processor.process_document(file_path, file_type)
            
            # Transform into session format
            paragraphs = []
            for chapter in result.get('chapters', []):
                for para in chapter.get('paragraphs', []):
                    if para.get('text'):  # Only include non-empty paragraphs
                        paragraphs.append({
                            'text': para['text'],
                            'chapter': chapter.get('number', 1),
                            'chapter_title': chapter.get('title', 'Chapter'),
                            'image_prompt': para.get('suggested_image_prompt', para['text']),
                            'image_url': None,
                            'audio_url': None
                        })
            
            if not paragraphs:
                raise ValueError("No valid paragraphs found in document")
            
            # Store in session
            session['book_data'] = {
                'type': 'processed_book',
                'filename': filename,
                'metadata': result.get('metadata', {}),
                'paragraphs': paragraphs
            }
            
            return jsonify({
                'success': True,
                'message': f'Successfully processed {len(paragraphs)} paragraphs',
                'metadata': result.get('metadata', {}),
                'redirect': '/doc/view'
            })
            
        finally:
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@doc_bp.route('/doc/view')
def view_document():
    if 'book_data' not in session:
        return redirect(url_for('doc.upload_document'))
    return render_template('document/view.html', book=session['book_data'])

@doc_bp.route('/doc/generate_media', methods=['POST'])
def generate_media():
    """Generate media for document paragraphs"""
    if 'book_data' not in session:
        return jsonify({'error': 'No book data found'}), 404
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
            
        start_index = data.get('start_index', 0)
        batch_size = min(data.get('batch_size', 5), 10)  # Limit batch size
        
        book_data = session['book_data']
        
        def generate():
            try:
                paragraphs = book_data['paragraphs'][start_index:start_index + batch_size]
                total = len(paragraphs)
                
                for i, paragraph in enumerate(paragraphs, 1):
                    current_index = start_index + i - 1
                    
                    try:
                        # Generate image
                        yield json.dumps({
                            'type': 'progress',
                            'step': 'image',
                            'message': f'Generating image for paragraph {i}/{total}',
                            'index': current_index
                        }) + '\n'
                        
                        image_url = image_generator.generate_image(paragraph['image_prompt'])
                        paragraph['image_url'] = image_url
                        
                        # Generate audio
                        yield json.dumps({
                            'type': 'progress',
                            'step': 'audio',
                            'message': f'Generating audio for paragraph {i}/{total}',
                            'index': current_index
                        }) + '\n'
                        
                        audio_url = audio_generator.generate_audio(paragraph['text'])
                        paragraph['audio_url'] = audio_url
                        
                        # Send update
                        yield json.dumps({
                            'type': 'update',
                            'index': current_index,
                            'data': paragraph
                        }) + '\n'
                        
                        # Update session
                        book_data['paragraphs'][current_index] = paragraph
                        session['book_data'] = book_data
                        
                    except Exception as e:
                        yield json.dumps({
                            'type': 'error',
                            'message': f'Error processing paragraph {i}: {str(e)}',
                            'index': current_index
                        }) + '\n'
                
                yield json.dumps({
                    'type': 'complete',
                    'message': f'Completed processing {total} paragraphs'
                }) + '\n'
                
            except Exception as e:
                yield json.dumps({
                    'type': 'error',
                    'message': str(e)
                }) + '\n'
        
        return Response(stream_with_context(generate()), mimetype='text/event-stream')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
