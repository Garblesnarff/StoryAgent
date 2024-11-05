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
                loadingOverlay.classList.remove('error');
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
                    if (!line || !line.startsWith('data:')) continue;
                    
                    try {
                        const jsonStr = line.replace('data:', '').trim();
                        if (!jsonStr) continue;
                        
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
                                        loadingOverlay.classList.add('error');
                                        const loadingText = loadingOverlay.querySelector('.loading-text');
                                        if (loadingText) {
                                            loadingText.classList.add('error');
                                            loadingText.textContent = data.message;
                                        }
                                    }
                                }
                                break;
                            case 'success':
                                if (data.redirect) {
                                    console.log('Redirecting to:', data.redirect);
                                    // Add a longer delay to ensure session is saved
                                    setTimeout(() => {
                                        window.location.href = data.redirect;
                                    }, 2000);
                                }
                                break;
                        }
                    } catch (error) {
                        console.error('Error parsing message:', error);
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
            if (loadingOverlay && !loadingOverlay.classList.contains('error')) {
                loadingOverlay.style.display = 'none';
            }
        }
    });
});

function updateAgentProgress(agent, status, message) {
    const agentProgress = document.getElementById('agent-progress');
    if (!agentProgress) return;

    let agentElement = document.getElementById(`progress-${agent.replace(/\s+/g, '-').toLowerCase()}`);
    if (!agentElement) {
        agentElement = document.createElement('div');
        agentElement.id = `progress-${agent.replace(/\s+/g, '-').toLowerCase()}`;
        agentElement.className = 'agent-progress-item';
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

    agentElement.className = `agent-progress-item ${statusClasses[status] || 'text-muted'}`;
    agentElement.innerHTML = `
        <div class="d-flex align-items-center gap-2">
            <div class="agent-status">
                ${statusIcons[status] || statusIcons.pending}
            </div>
            <div class="agent-info">
                <div class="agent-name">${agent}</div>
                <div class="agent-message small">${message}</div>
            </div>
        </div>
    `;

    // Auto-scroll to the latest progress
    agentProgress.scrollTop = agentProgress.scrollHeight;
}
