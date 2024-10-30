document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');
    const logContent = document.getElementById('log-content');

    function addLogMessage(message) {
        const logEntry = document.createElement('div');
        logEntry.textContent = message;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }

    // Story generation form submission
    storyForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        logContent.innerHTML = '';
        
        try {
            const formData = new FormData(storyForm);
            addLogMessage('Generating story...');
            
            const response = await fetch('/generate_story', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Story generation failed');
            }

            if (data.success && data.redirect) {
                window.location.href = data.redirect;
            } else {
                throw new Error(data.error || 'Invalid response from server');
            }
        } catch (error) {
            console.error('Error:', error);
            addLogMessage('Error: ' + error.message);
        }
    });
});
