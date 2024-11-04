document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');

    storyForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        try {
            const formData = new FormData(storyForm);
            const loadingOverlay = document.getElementById('loading-overlay');
            const agentProgress = document.getElementById('agent-progress');
            
            if (loadingOverlay) {
                loadingOverlay.style.display = 'flex';
            }

            if (agentProgress) {
                agentProgress.innerHTML = ''; // Clear previous progress
                
                // Update progress with each agent's status
                const updateProgress = (step, status) => {
                    const stepDiv = document.createElement('div');
                    stepDiv.className = `agent-progress-step ${status}`;
                    stepDiv.textContent = step;
                    agentProgress.appendChild(stepDiv);
                };

                // Initial progress steps
                updateProgress('Concept Generator: Creating story concept...', 'active');
                updateProgress('World Builder: Building story world...', 'pending');
                updateProgress('Plot Weaver: Developing plot structure...', 'pending');
            }

            const response = await fetch('/generate_story', {
                method: 'POST',
                body: formData
            });

            let data;
            try {
                data = await response.json();
            } catch (parseError) {
                console.error('Failed to parse JSON response:', parseError);
                throw new Error('Server returned an invalid response');
            }
            
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
            alert('Error: ' + (error.message || 'An unexpected error occurred'));
        } finally {
            const loadingOverlay = document.getElementById('loading-overlay');
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
        }
    });
});
