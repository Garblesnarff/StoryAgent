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
    current_app.logger.debug(f"Session data: {dict(session)}")
    
    if 'story_data' not in session:
        current_app.logger.error("No story data in session")
        flash('No story data found. Please generate or upload a story first.')
        return redirect(url_for('index'))
        
    story_data = session.get('story_data')
    current_app.logger.info(f"Retrieved story data with {len(story_data.get('paragraphs', []))} paragraphs")
    
    # Ensure story data has required fields
    if not story_data or 'paragraphs' not in story_data:
        current_app.logger.error("Invalid story data structure")
        flash('Invalid story data. Please try uploading again.')
        return redirect(url_for('index'))
    
    # Make session permanent
    session.permanent = True
    session.modified = True
    
    return render_template('story/edit.html', story=story_data)

@story_bp.route('/story/update_paragraph', methods=['POST'])
def update_paragraph():
    try:
        # Check if story data exists in session
        if 'story_data' not in session:
            current_app.logger.error("No story data found in session")
            return jsonify({'error': 'No story data found'}), 404

        data = request.get_json()
        text = data.get('text')
        index = data.get('index')
        
        if not text or index is None:
            current_app.logger.error("Invalid data provided for paragraph update")
            return jsonify({'error': 'Invalid data provided'}), 400
            
        # Update story in session
        story_data = session['story_data']
        if index >= len(story_data['paragraphs']):
            current_app.logger.error(f"Invalid paragraph index: {index}")
            return jsonify({'error': 'Invalid paragraph index'}), 400
            
        story_data['paragraphs'][index]['text'] = text
        session['story_data'] = story_data
        session.permanent = True
        session.modified = True
        
        current_app.logger.info(f"Updated paragraph {index} with new text")
        
        # Generate new image and audio if requested
        if data.get('generate_media', False):
            current_app.logger.info(f"Generating media for paragraph {index}")
            image_url = image_service.generate_image(text)
            audio_url = audio_service.generate_audio(text)
            
            # Update media URLs in session
            story_data['paragraphs'][index]['image_url'] = image_url
            story_data['paragraphs'][index]['audio_url'] = audio_url
            session['story_data'] = story_data
            session.modified = True
            
            current_app.logger.info(f"Generated media for paragraph {index}")
            
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
        current_app.logger.error(f"Error updating paragraph: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
