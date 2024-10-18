document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');
    const storyOutput = document.getElementById('story-output');
    const storyContent = document.getElementById('story-content');
    const storyImage = document.getElementById('story-image');
    const storyAudio = document.getElementById('story-audio');
    const playAudioBtn = document.getElementById('play-audio');
    const saveStoryBtn = document.getElementById('save-story');

    storyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(storyForm);
        
        try {
            const response = await fetch('/generate_story', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to generate story');
            }
            
            const data = await response.json();
            
            if (!data.story || !data.image_url || !data.audio_url) {
                throw new Error('Incomplete data received from server');
            }
            
            storyContent.textContent = data.story;
            storyImage.src = data.image_url;
            storyAudio.src = data.audio_url;
            
            storyOutput.style.display = 'block';
        } catch (error) {
            console.error('Error:', error.message);
            alert(`An error occurred while generating the story: ${error.message}`);
        }
    });

    playAudioBtn.addEventListener('click', () => {
        storyAudio.play();
    });

    saveStoryBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/save_story', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prompt: document.getElementById('prompt').value,
                    story: storyContent.textContent,
                    image_url: storyImage.src,
                    audio_url: storyAudio.src
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to save story');
            }
            
            alert('Story saved successfully!');
        } catch (error) {
            console.error('Error:', error.message);
            alert(`An error occurred while saving the story: ${error.message}`);
        }
    });
});
