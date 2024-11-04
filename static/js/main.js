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

            // Clear previous progress
            if (agentProgress) {
                agentProgress.innerHTML = '';
            }

            const response = await fetch('/generate_story', {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'text/event-stream'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');

                for (let i = 0; i < lines.length - 1; i++) {
                    const line = lines[i].trim();
                    if (!line) continue;

                    try {
                        const data = JSON.parse(line);
                        switch (data.type) {
                            case 'agent_progress':
                                updateAgentProgress(data.agent, data.status, data.message);
                                break;
                            case 'success':
                                if (data.redirect) {
                                    window.location.href = data.redirect;
                                }
                                break;
                            case 'error':
                                throw new Error(data.message || 'An unknown error occurred');
                        }
                    } catch (parseError) {
                        console.error('Error parsing progress:', parseError, line);
                    }
                }
                buffer = lines[lines.length - 1];
            }

        } catch (error) {
            console.error('Error:', error.message || error);
            
            // Update progress display with error state
            const errorMessage = error.message || 'An unexpected error occurred';
            updateAgentProgress('Story Generation', 'error', errorMessage);
            
            // Show error in alert
            alert('Error: ' + errorMessage);
        } finally {
            const loadingOverlay = document.getElementById('loading-overlay');
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
        }
    });
});

function updateAgentProgress(agent, status, message) {
    const agentProgress = document.getElementById('agent-progress');
    if (!agentProgress) {
        const progressContainer = document.createElement('div');
        progressContainer.id = 'agent-progress';
        progressContainer.className = 'progress-container';
        document.querySelector('.content-wrapper')?.appendChild(progressContainer);
    }

    let agentElement = document.getElementById(`progress-${agent}`);
    if (!agentElement) {
        agentElement = document.createElement('div');
        agentElement.id = `progress-${agent}`;
        agentElement.className = 'agent-progress-item';
        document.getElementById('agent-progress')?.appendChild(agentElement);
    }

    const statusClasses = {
        'pending': 'text-muted',
        'active': 'text-primary',
        'completed': 'text-success',
        'error': 'text-danger'
    };

    agentElement.className = `agent-progress-item ${statusClasses[status] || 'text-muted'}`;
    agentElement.innerHTML = `
        <div class="d-flex align-items-center gap-2">
            <div class="agent-status">
                ${status === 'active' ? '<div class="spinner-border spinner-border-sm"></div>' :
                 status === 'completed' ? '<i class="bi bi-check-circle-fill"></i>' :
                 status === 'error' ? '<i class="bi bi-x-circle-fill"></i>' : '○'}
            </div>
            <div class="agent-info">
                <div class="agent-name">${agent}</div>
                <div class="agent-message small">${message}</div>
            </div>
        </div>
    `;
}
