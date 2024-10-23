document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');
    const storyOutput = document.getElementById('story-output');
    const paragraphCards = document.getElementById('paragraph-cards');
    const saveStoryBtn = document.getElementById('save-story');
    const logContent = document.getElementById('log-content');

    function addLogMessage(message) {
        const logEntry = document.createElement('div');
        logEntry.textContent = message;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }

    function addParagraphCard(paragraph) {
        const card = document.createElement('div');
        card.className = 'col';
        card.innerHTML = `
            <div class="card h-100">
                <img src="${paragraph.image_url}" class="card-img-top" alt="Paragraph image">
                <div class="card-body">
                    <p class="card-text">${paragraph.text}</p>
                </div>
                <div class="card-footer">
                    <audio controls src="${paragraph.audio_url}"></audio>
                </div>
            </div>
        `;
        paragraphCards.appendChild(card);
        storyOutput.style.display = 'block';
        setupAudioHover();
    }

    function setupAudioHover() {
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            const audio = card.querySelector('audio');
            card.addEventListener('mouseenter', () => audio.play());
            card.addEventListener('mouseleave', () => audio.pause());
        });
    }

    storyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(storyForm);
        
        try {
            logContent.innerHTML = '';
            paragraphCards.innerHTML = '';
            storyOutput.style.display = 'none';
            
            addLogMessage("Generating story...");
            
            const response = await fetch('/generate_story', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to generate story');
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error('Invalid data received from server');
            }
            
            // Display all paragraphs
            data.paragraphs.forEach(paragraph => {
                addLogMessage(`Processing paragraph: ${paragraph.text.substring(0, 50)}...`);
                addParagraphCard(paragraph);
            });
            
            addLogMessage("Story generation complete!");
        } catch (error) {
            console.error('Error:', error.message);
            addLogMessage(`Error: ${error.message}`);
            alert(`An error occurred while generating the story: ${error.message}`);
        }
    });

    saveStoryBtn.addEventListener('click', async () => {
        try {
            const paragraphs = Array.from(paragraphCards.children).map(card => ({
                text: card.querySelector('.card-text').textContent,
                image_url: card.querySelector('.card-img-top').src,
                audio_url: card.querySelector('audio').src
            }));

            const response = await fetch('/save_story', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prompt: document.getElementById('prompt').value,
                    genre: document.getElementById('genre').value,
                    mood: document.getElementById('mood').value,
                    target_audience: document.getElementById('target_audience').value,
                    paragraphs: document.getElementById('paragraphs').value,
                    story_paragraphs: paragraphs
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

    // Initial setup for any existing cards
    setupAudioHover();
});
