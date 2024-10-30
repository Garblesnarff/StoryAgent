from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
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

@story.route('/update_paragraph', methods=['POST'])
def update_paragraph():
    try:
        data = request.get_json()
        text = data.get('text')
        index = data.get('index')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        # Only update text in session
        if 'story_paragraphs' in session:
            story_paragraphs = session['story_paragraphs']
            if 0 <= index < len(story_paragraphs):
                story_paragraphs[index] = text
                session['story_paragraphs'] = story_paragraphs
                session.modified = True
                
                # Clear media cache
                if 'story_media' in session:
                    del session['story_media']
                    
        return jsonify({
            'success': True,
            'text': text
        })
    except Exception as e:
        print(f"Error updating paragraph: {str(e)}")
        return jsonify({'error': str(e)}), 500

@story.route('/generate', methods=['GET'])
def generate():
    if 'story_paragraphs' not in session:
        return redirect(url_for('main.index'))
    
    try:
        paragraphs = session.get('story_paragraphs', [])
        print(f"Loading generate page with {len(paragraphs)} paragraphs")  # Debug log
        
        if not paragraphs:
            return redirect(url_for('story.edit'))
            
        # Show loading template
        return render_template('story/generate.html', 
                             story_cards=[],
                             is_loading=True,
                             total_paragraphs=len(paragraphs))
                             
    except Exception as e:
        print(f"Error in generate route: {str(e)}")
        return redirect(url_for('story.edit'))

@story.route('/generate_media')
def generate_media():
    try:
        if 'story_paragraphs' not in session:
            print("No story found in session")  # Debug log
            return jsonify({'error': 'No story found'}), 404
            
        paragraphs = session.get('story_paragraphs', [])
        print(f"Generating media for {len(paragraphs)} paragraphs")  # Debug log
        story_media = []
        
        for idx, text in enumerate(paragraphs):
            try:
                print(f"Generating media for paragraph {idx + 1}")  # Debug log
                image_url = image_service.generate_image(text)
                audio_url = audio_service.generate_audio(text)
                
                if not image_url or not audio_url:
                    print(f"Failed to generate media for paragraph {idx + 1}")  # Debug log
                    raise Exception('Failed to generate media')
                    
                story_media.append({
                    'text': text,
                    'image_url': image_url,
                    'audio_url': audio_url
                })
                print(f"Successfully generated media for paragraph {idx + 1}")  # Debug log
                
            except Exception as e:
                print(f'Error generating media for paragraph {idx}: {str(e)}')
                return jsonify({'error': f'Failed to generate media for paragraph {idx + 1}'}), 500
        
        session['story_media'] = story_media
        session.modified = True
        print("Successfully generated all media")  # Debug log
        return jsonify({'success': True, 'story_media': story_media})
        
    except Exception as e:
        print(f'Error in generate_media: {str(e)}')
        return jsonify({'error': str(e)}), 500
