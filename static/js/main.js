document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');
    const storyOutput = document.getElementById('story-output');
    const paragraphCards = document.getElementById('paragraph-cards');
    const saveStoryBtn = document.getElementById('save-story');
    const logContent = document.getElementById('log-content');
    const editModal = new bootstrap.Modal(document.getElementById('editModal'));
    let currentEditingCard = null;

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
            addLogMessage('Updating paragraph...');
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
            addLogMessage('Regenerating image...');
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
            addLogMessage('Regenerating audio...');
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
            
            const response = await fetch('/generate_story', {
                method: 'POST',
                body: formData
            });
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const text = decoder.decode(value);
                const lines = text.split('\n');
                
                for (const line of lines) {
                    if (!line.trim()) continue;
                    
                    try {
                        const data = JSON.parse(line);
                        
                        switch (data.type) {
                            case 'log':
                                addLogMessage(data.message);
                                break;
                                
                            case 'paragraph':
                                addParagraphCard(data.data, data.data.index);
                                setupAudioHover();
                                break;
                                
                            case 'rate_limit':
                                addLogMessage(data.message);
                                break;
                                
                            case 'error':
                                addLogMessage(`Error: ${data.message}`);
                                alert(`An error occurred: ${data.message}`);
                                break;
                                
                            case 'complete':
                                addLogMessage(data.message);
                                break;
                        }
                    } catch (parseError) {
                        console.error('Error parsing message:', parseError);
                    }
                }
            }
        } catch (error) {
            console.error('Error:', error);
            addLogMessage(`Error: ${error.message}`);
            alert(`An error occurred: ${error.message}`);
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
                throw new Error('Failed to save story');
            }
            
            alert('Story saved successfully!');
        } catch (error) {
            console.error('Error:', error);
            alert(`An error occurred while saving the story: ${error.message}`);
        }
    });

    // Initial setup for any existing cards
    setupAudioHover();
});
