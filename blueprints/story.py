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
    if 'story_data' not in session:
        return redirect(url_for('index'))
    return render_template('story/edit.html', story=session['story_data'])

@story_bp.route('/story/update_paragraph', methods=['POST'])
def update_paragraph():
    try:
        data = request.get_json()
        text = data.get('text')
        index = data.get('index')
        
        if not text or index is None:
            return jsonify({'error': 'Invalid data provided'}), 400
            
        # Update story in session
        if 'story_data' in session:
            story_data = session['story_data']
            story_data['paragraphs'][index]['text'] = text
            session['story_data'] = story_data
            
            # Generate new image and audio
            image_url = image_service.generate_image(text)
            audio_url = audio_service.generate_audio(text)
            
            # Update media URLs in session
            story_data['paragraphs'][index]['image_url'] = image_url
            story_data['paragraphs'][index]['audio_url'] = audio_url
            session['story_data'] = story_data
            
            return jsonify({
                'success': True,
                'text': text,
                'image_url': image_url,
                'audio_url': audio_url
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@story_bp.route('/story/regenerate_image', methods=['POST'])
def regenerate_image():
    try:
        data = request.get_json()
        text = data.get('text')
        index = data.get('index')
        
        if not text or index is None:
            return jsonify({'error': 'Invalid data provided'}), 400
            
        image_url = regeneration_service.regenerate_image(text)
        
        # Update image URL in session
        if 'story_data' in session:
            story_data = session['story_data']
            story_data['paragraphs'][index]['image_url'] = image_url
            session['story_data'] = story_data
            
        return jsonify({
            'success': True,
            'image_url': image_url
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@story_bp.route('/story/regenerate_audio', methods=['POST'])
def regenerate_audio():
    try:
        data = request.get_json()
        text = data.get('text')
        index = data.get('index')
        
        if not text or index is None:
            return jsonify({'error': 'Invalid data provided'}), 400
            
        audio_url = regeneration_service.regenerate_audio(text)
        
        # Update audio URL in session
        if 'story_data' in session:
            story_data = session['story_data']
            story_data['paragraphs'][index]['audio_url'] = audio_url
            session['story_data'] = story_data
            
        return jsonify({
            'success': True,
            'audio_url': audio_url
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
