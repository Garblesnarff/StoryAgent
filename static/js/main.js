document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');
    const storyOutput = document.getElementById('story-output');
    const paragraphCards = document.getElementById('paragraph-cards');
    const saveStoryBtn = document.getElementById('save-story');
    const logContent = document.getElementById('log-content');
    const editModal = new bootstrap.Modal(document.getElementById('editModal'));
    let currentEditingCard = null;

    // Connect to Socket.IO
    const socket = io();

    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('generation_progress', (data) => {
        addLogMessage(data.message);
    });

    function addLogMessage(message) {
        const logEntry = document.createElement('div');
        logEntry.textContent = message;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }

    function addParagraphCard(paragraph, index) {
        const card = document.createElement('div');
        card.className = 'col';
        card.innerHTML = `
            <div class="card h-100">
                <img src="${paragraph.image_url}" class="card-img-top" alt="Paragraph image">
                <div class="card-body">
                    <p class="card-text">${paragraph.text}</p>
                    <button class="btn btn-primary edit-paragraph" data-index="${index}">Edit</button>
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

    // Handle edit button clicks
    paragraphCards.addEventListener('click', async (e) => {
        if (e.target.classList.contains('edit-paragraph')) {
            const index = e.target.dataset.index;
            const card = e.target.closest('.card');
            currentEditingCard = card;
            
            const paragraphText = card.querySelector('.card-text').textContent;
            document.getElementById('editParagraphText').value = paragraphText;
            editModal.show();
        }
    });

    // Handle paragraph edit save
    document.getElementById('saveParagraphEdit').addEventListener('click', async () => {
        if (!currentEditingCard) return;

        const newText = document.getElementById('editParagraphText').value;
        const paragraphElement = currentEditingCard.querySelector('.card-text');
        
        try {
            const response = await fetch('/update_paragraph', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: newText
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update paragraph');
            }

            const data = await response.json();
            paragraphElement.textContent = newText;

            if (data.image_url) {
                currentEditingCard.querySelector('.card-img-top').src = data.image_url;
            }
            if (data.audio_url) {
                currentEditingCard.querySelector('audio').src = data.audio_url;
            }

            editModal.hide();
            addLogMessage('Paragraph updated successfully!');
        } catch (error) {
            console.error('Error:', error);
            addLogMessage(`Error updating paragraph: ${error.message}`);
            alert('Failed to update paragraph. Please try again.');
        }
    });

    // Regenerate image button
    document.getElementById('regenerateImage').addEventListener('click', async () => {
        if (!currentEditingCard) return;

        try {
            const text = document.getElementById('editParagraphText').value;
            const response = await fetch('/regenerate_image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                throw new Error('Failed to regenerate image');
            }

            const data = await response.json();
            currentEditingCard.querySelector('.card-img-top').src = data.image_url;
            addLogMessage('Image regenerated successfully!');
        } catch (error) {
            console.error('Error:', error);
            addLogMessage(`Error regenerating image: ${error.message}`);
            alert('Failed to regenerate image. Please try again.');
        }
    });

    // Regenerate audio button
    document.getElementById('regenerateAudio').addEventListener('click', async () => {
        if (!currentEditingCard) return;

        try {
            const text = document.getElementById('editParagraphText').value;
            const response = await fetch('/regenerate_audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                throw new Error('Failed to regenerate audio');
            }

            const data = await response.json();
            currentEditingCard.querySelector('audio').src = data.audio_url;
            addLogMessage('Audio regenerated successfully!');
        } catch (error) {
            console.error('Error:', error);
            addLogMessage(`Error regenerating audio: ${error.message}`);
            alert('Failed to regenerate audio. Please try again.');
        }
    });

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
            data.paragraphs.forEach((paragraph, index) => {
                addLogMessage(`Processing paragraph: ${paragraph.text.substring(0, 50)}...`);
                addParagraphCard(paragraph, index);
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
