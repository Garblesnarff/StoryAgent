from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, current_app, flash
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
    # Log session data for debugging
    current_app.logger.info("Accessing edit page")
    current_app.logger.debug(f"Session data: {list(session.keys())}")
    
    if 'story_data' not in session:
        flash('No story data found. Please generate or upload a story first.')
        return redirect(url_for('index'))
        
    story_data = session['story_data']
    # Ensure story data has required fields
    if 'paragraphs' not in story_data:
        flash('Invalid story data. Please try uploading again.')
        return redirect(url_for('index'))
        
    # Add source information if missing
    if 'source' not in story_data:
        story_data['source'] = 'generated'
    
    # Make session permanent
    session.permanent = True
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
        session.permanent = True
        
        # Generate new image and audio if requested
        if data.get('generate_media', False):
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
        
        return jsonify({
            'success': True,
            'text': text
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
