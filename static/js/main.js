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
                // Initialize all agents as pending
                const agents = ['Concept Generator', 'World Builder', 'Plot Weaver', 'Story Generator'];
                agents.forEach(agent => {
                    updateAgentProgress(agent, 'pending', 'Waiting to start...');
                });
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
                        // Extract JSON data from SSE format
                        const match = line.match(/^data:\s*(.+)$/);
                        if (!match) continue;

                        const data = JSON.parse(match[1]);
                        
                        switch (data.type) {
                            case 'agent_progress':
                                if (data.agent && data.status && data.message) {
                                    console.log(`Agent Progress: ${data.agent} - ${data.status} - ${data.message}`);
                                    updateAgentProgress(data.agent, data.status, data.message);
                                }
                                break;
                            case 'error':
                                if (data.message) {
                                    console.error('Generation Error:', data.message);
                                    updateAgentProgress('Story Generation', 'error', data.message);
                                    if (loadingOverlay) {
                                        loadingOverlay.style.display = 'none';
                                    }
                                    throw new Error(data.message);
                                }
                                break;
                            case 'success':
                                if (data.redirect) {
                                    // Mark all agents as completed before redirecting
                                    const agents = document.querySelectorAll('.agent-progress-item');
                                    agents.forEach(agent => {
                                        if (!agent.classList.contains('text-success') && !agent.classList.contains('text-danger')) {
                                            const agentName = agent.querySelector('.agent-name')?.textContent;
                                            if (agentName) {
                                                updateAgentProgress(agentName, 'completed', 'Task completed successfully');
                                            }
                                        }
                                    });
                                    setTimeout(() => {
                                        window.location.href = data.redirect;
                                    }, 1000); // Small delay to show completion
                                }
                                break;
                        }
                    } catch (error) {
                        console.error('Error parsing progress:', error, line);
                        if (line.includes('error')) {
                            updateAgentProgress('Story Generation', 'error', 'Failed to process server response');
                        }
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
        'pending': '<i class="bi bi-clock"></i>',
        'active': '<div class="spinner-border spinner-border-sm"></div>',
        'completed': '<i class="bi bi-check-circle-fill"></i>',
        'error': '<i class="bi bi-x-circle-fill"></i>'
    };

    const statusClass = statusClasses[status] || 'text-muted';
    const statusIcon = statusIcons[status] || '<i class="bi bi-clock"></i>';

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

    // Add visual feedback for different states
    switch (status) {
        case 'error':
            agentElement.classList.add('border', 'border-danger', 'rounded', 'p-2');
            break;
        case 'completed':
            agentElement.classList.add('border', 'border-success', 'rounded', 'p-2');
            // Add completion animation
            agentElement.style.animation = 'fadeInScale 0.3s ease-out';
            break;
        case 'active':
            agentElement.classList.add('border', 'border-primary', 'rounded', 'p-2');
            break;
    }
}
