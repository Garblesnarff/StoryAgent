document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');
    const storyOutput = document.getElementById('story-output');
    const paragraphCards = document.getElementById('paragraph-cards');
    const saveStoryBtn = document.getElementById('save-story');
    const logContent = document.getElementById('log-content');

    let socket = io();

    socket.on('log_message', function(data) {
        addLogMessage(data.message);
    });

    function addLogMessage(message) {
        const logEntry = document.createElement('div');
        logEntry.textContent = message;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }

    storyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(storyForm);
        
        try {
            logContent.innerHTML = '';
            
            const response = await fetch('/generate_story', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to generate story');
            }
            
            const data = await response.json();
            
            if (!data.paragraphs || !Array.isArray(data.paragraphs)) {
                throw new Error('Invalid data received from server');
            }
            
            // Clear previous content
            paragraphCards.innerHTML = '';
            
            // Create a card for each paragraph
            data.paragraphs.forEach((paragraph, index) => {
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
            });
            
            storyOutput.style.display = 'block';
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
                    paragraphs: paragraphs
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
