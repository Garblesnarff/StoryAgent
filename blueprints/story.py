from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from services.text_generator import TextGenerator
from services.image_generator import ImageGenerator
from services.hume_audio_generator import HumeAudioGenerator
from services.regeneration_service import RegenerationService

story_bp = Blueprint('story', __name__)
text_service = TextGenerator()
image_service = ImageGenerator()
audio_service = HumeAudioGenerator()
regeneration_service = RegenerationService(image_service, audio_service)

@story_bp.route('/story/edit', methods=['GET'])
def edit():
    story_data = session.get('story_data')
    if not story_data:
        return redirect(url_for('index'))
    
    # Ensure story data structure is complete
    if 'paragraphs' not in story_data:
        return redirect(url_for('index'))
        
    # Ensure session is saved
    session.modified = True
    return render_template('story/edit.html', story=story_data)

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
        session.modified = True  # Force session save
        
        # Generate new image and audio if requested
        if data.get('generate_media', False):
            image_url = image_service.generate_image(text)
            audio_url = audio_service.generate_audio(text)
            
            # Update media URLs in session
            story_data['paragraphs'][index]['image_url'] = image_url
            story_data['paragraphs'][index]['audio_url'] = audio_url
            session['story_data'] = story_data
            session.modified = True  # Force session save
            
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
