from flask import Blueprint, render_template, request, jsonify, session
from services.text_generator import TextGenerator
from services.image_generator import ImageGenerator
from services.hume_audio_generator import HumeAudioGenerator

story = Blueprint('story', __name__)
text_service = TextGenerator()
image_service = ImageGenerator()
audio_service = HumeAudioGenerator()

@story.route('/edit', methods=['POST'])
def edit():
    if request.method == 'POST':
        # Store form data in session
        session['story_data'] = {
            'prompt': request.form.get('prompt'),
            'genre': request.form.get('genre'),
            'mood': request.form.get('mood'),
            'target_audience': request.form.get('target_audience'),
            'paragraphs': request.form.get('paragraphs', 5)
        }
        # Generate initial story
        paragraphs = text_service.generate_story(
            session['story_data']['prompt'],
            session['story_data']['genre'],
            session['story_data']['mood'],
            session['story_data']['target_audience'],
            int(session['story_data']['paragraphs'])
        )
        session['story_paragraphs'] = paragraphs
        return render_template('story/edit.html', paragraphs=paragraphs)
    return render_template('story/edit.html')

@story.route('/generate')
def generate():
    return render_template('story/generate.html')

@story.route('/update_paragraph', methods=['POST'])
def update_paragraph():
    try:
        data = request.get_json()
        text = data.get('text')
        index = data.get('index')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        # Update paragraph in session
        if 'story_paragraphs' in session:
            story_paragraphs = session['story_paragraphs']
            if 0 <= index < len(story_paragraphs):
                story_paragraphs[index] = text
                session['story_paragraphs'] = story_paragraphs
            
        # Generate new image and audio
        image_url = image_service.generate_image(text)
        audio_url = audio_service.generate_audio(text)
        
        return jsonify({
            'success': True,
            'text': text,
            'image_url': image_url,
            'audio_url': audio_url
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
