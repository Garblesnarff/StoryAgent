document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');
    const storyOutput = document.getElementById('story-output');
    const paragraphCards = document.getElementById('paragraph-cards');
    const saveStoryBtn = document.getElementById('save-story');
    const logContent = document.getElementById('log-content');
    const progressBar = document.getElementById('progress-bar');
    const progressContainer = document.getElementById('progress-container');

    const socket = io('/', { 
        path: '/socket.io',
        transports: ['websocket', 'polling'],
        reconnectionAttempts: 5,
        reconnectionDelay: 1000
    });

    socket.on('connect', () => {
        console.log('Connected to Socket.IO server');
        addLogMessage('Connected to server');
    });

    socket.on('connect_error', (error) => {
        console.error('Socket.IO connection error:', error);
        addLogMessage('Error: Unable to connect to the server. Retrying...');
    });

    socket.on('disconnect', (reason) => {
        console.log('Disconnected from Socket.IO server:', reason);
        addLogMessage('Disconnected from server. Attempting to reconnect...');
    });

    socket.on('reconnect', (attemptNumber) => {
        console.log('Reconnected to Socket.IO server after', attemptNumber, 'attempts');
        addLogMessage('Reconnected to server');
    });

    socket.on('reconnect_failed', () => {
        console.error('Failed to reconnect to Socket.IO server');
        addLogMessage('Error: Failed to reconnect to the server. Please refresh the page.');
    });

    socket.on('log_message', function(data) {
        addLogMessage(data.message);
        if (data.progress) {
            updateProgressBar(data.progress.current, data.progress.total);
        }
    });

    socket.on('new_paragraph', function(data) {
        addParagraphCard(data);
    });

    socket.on('total_paragraphs', function(data) {
        initializeProgressBar(data.total);
    });

    function addLogMessage(message) {
        const logEntry = document.createElement('div');
        logEntry.textContent = message;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }

    function initializeProgressBar(total) {
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', 0);
        progressBar.setAttribute('aria-valuemax', total);
        progressContainer.style.display = 'block';
    }

    function updateProgressBar(current, total) {
        const percentage = (current / total) * 100;
        progressBar.style.width = `${percentage}%`;
        progressBar.setAttribute('aria-valuenow', current);
        progressBar.textContent = `${current} / ${total}`;
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
                ${paragraph.audio_url ? `
                <div class="card-footer">
                    <audio controls src="${paragraph.audio_url}"></audio>
                </div>
                ` : ''}
            </div>
        `;
        paragraphCards.appendChild(card);
        storyOutput.style.display = 'block';
    }

    storyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(storyForm);
        
        try {
            logContent.innerHTML = '';
            paragraphCards.innerHTML = '';
            storyOutput.style.display = 'none';
            progressContainer.style.display = 'none';
            
            const response = await fetch('/generate_story', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to generate story');
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error('Invalid data received from server');
            }
            
            // The paragraphs will be added by the socket.on('new_paragraph') listener
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
                audio_url: card.querySelector('audio')?.src || ''
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
                throw new Error(errorData.message || 'Failed to save story');
            }
            
            alert('Story saved successfully!');
        } catch (error) {
            console.error('Error:', error.message);
            alert(`An error occurred while saving the story: ${error.message}`);
        }
    });
});
