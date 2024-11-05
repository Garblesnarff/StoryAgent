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
                    if (!line || !line.startsWith('data:')) continue;
                    
                    try {
                        const jsonStr = line.replace('data:', '').trim();
                        const data = JSON.parse(jsonStr);
                        
                        switch (data.type) {
                            case 'agent_progress':
                                if (data.agent && data.status && data.message) {
                                    updateAgentProgress(data.agent, data.status, data.message);
                                }
                                break;
                            case 'error':
                                if (data.message) {
                                    updateAgentProgress('Story Generation', 'error', data.message);
                                    if (loadingOverlay) {
                                        loadingOverlay.style.display = 'none';
                                    }
                                    throw new Error(data.message);
                                }
                                break;
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
        agentElement.className = 'agent-progress-item mb-2';
        agentProgress.appendChild(agentElement);
    }

    const statusClasses = {
        'pending': 'text-muted',
        'active': 'text-primary',
        'completed': 'text-success',
        'error': 'text-danger'
    };

    const statusIcons = {
        'pending': '○',
        'active': '<div class="spinner-border spinner-border-sm"></div>',
        'completed': '<i class="bi bi-check-circle-fill"></i>',
        'error': '<i class="bi bi-x-circle-fill"></i>'
    };

    const statusClass = statusClasses[status] || 'text-muted';
    const statusIcon = statusIcons[status] || '○';

    agentElement.className = `agent-progress-item mb-2 ${statusClass}`;
    agentElement.innerHTML = `
        <div class="d-flex align-items-center gap-2">
            <div class="agent-status">
                ${statusIcon}
            </div>
            <div class="agent-info">
                <div class="agent-name fw-bold">${agent}</div>
                <div class="agent-message small text-wrap">${message}</div>
            </div>
        </div>
    `;

    // If there's an error, add an alert class
    if (status === 'error') {
        agentElement.classList.add('border', 'border-danger', 'rounded', 'p-2');
    }
}
