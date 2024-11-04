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
                body: formData
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
                        // Remove 'data: ' prefix if it exists
                        const jsonStr = line.startsWith('data:') ? line.substring(5).trim() : line;
                        const data = JSON.parse(jsonStr);
                        
                        switch (data.type) {
                            case 'agent_progress':
                                updateAgentProgress(data.agent, data.status, data.message);
                                break;
                            case 'error':
                                updateAgentProgress('Story Generation', 'error', data.message);
                                if (loadingOverlay) {
                                    loadingOverlay.style.display = 'none';
                                }
                                throw new Error(data.message);
                            case 'success':
                                if (data.redirect) {
                                    window.location.href = data.redirect;
                                }
                                break;
                        }
                    } catch (error) {
                        console.error('Error parsing progress:', error, line);
                        updateAgentProgress('Story Generation', 'error', error.message || 'Failed to generate story');
                    }
                }
                buffer = lines[lines.length - 1];
            }

        } catch (error) {
            console.error('Error:', error.message || error);
            updateAgentProgress('Story Generation', 'error', error.message || 'An unexpected error occurred');
            alert('Error: ' + (error.message || 'An unexpected error occurred'));
        } finally {
            const loadingOverlay = document.getElementById('loading-overlay');
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
        }
    });
});

function updateAgentProgress(agent, status, message) {
    let agentProgress = document.getElementById('agent-progress');
    if (!agentProgress) {
        agentProgress = document.createElement('div');
        agentProgress.id = 'agent-progress';
        agentProgress.className = 'progress-container mt-4';
        document.querySelector('.content-wrapper')?.appendChild(agentProgress);
    }

    let agentElement = document.getElementById(`progress-${agent.replace(/\s+/g, '-')}`);
    if (!agentElement) {
        agentElement = document.createElement('div');
        agentElement.id = `progress-${agent.replace(/\s+/g, '-')}`;
        agentElement.className = 'agent-progress-item';
        agentProgress.appendChild(agentElement);
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
