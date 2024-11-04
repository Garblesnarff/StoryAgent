document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');
    
    // Agent progress handling
    function updateAgentProgress(agentId, status, progress, task) {
        const agentElement = document.getElementById(agentId);
        if (!agentElement) return;
        
        // Update status classes
        const agents = document.querySelectorAll('.agent-status');
        agents.forEach(agent => {
            agent.classList.remove('active');
            if (status === 'completed') {
                agent.classList.remove('error');
            }
        });
        
        // Update current agent status
        if (status === 'active') {
            agentElement.classList.add('active');
        } else if (status === 'completed') {
            agentElement.classList.add('completed');
        } else if (status === 'error') {
            agentElement.classList.add('error');
        }
        
        // Update progress bar
        const progressBar = agentElement.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
        }
        
        // Update task text
        const taskElement = agentElement.querySelector('.agent-task');
        if (taskElement && task) {
            taskElement.textContent = task;
        }
    }
    
    function updateOverallProgress(progress) {
        const progressBar = document.querySelector('.overall-progress .progress-bar');
        const progressText = document.querySelector('.overall-progress .progress-text');
        
        if (progressBar && progressText) {
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
            progressText.textContent = `Overall Progress: ${progress}%`;
        }
    }
    
    // Event listener for SSE messages
    function handleProgressEvent(event) {
        try {
            const data = JSON.parse(event.data);
            
            if (data.agent && data.status) {
                updateAgentProgress(data.agent, data.status, data.progress || 0, data.task);
                if (data.overall_progress) {
                    updateOverallProgress(data.overall_progress);
                }
            }
        } catch (error) {
            console.error('Error parsing progress event:', error);
        }
    }

    storyForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        try {
            const formData = new FormData(storyForm);
            const loadingOverlay = document.getElementById('loading-overlay');
            
            if (loadingOverlay) {
                loadingOverlay.style.display = 'flex';
                
                // Reset all agents to initial state
                document.querySelectorAll('.agent-status').forEach(agent => {
                    agent.classList.remove('active', 'completed', 'error');
                    const progressBar = agent.querySelector('.progress-bar');
                    if (progressBar) {
                        progressBar.style.width = '0%';
                        progressBar.setAttribute('aria-valuenow', 0);
                    }
                    const taskElement = agent.querySelector('.agent-task');
                    if (taskElement) {
                        taskElement.textContent = 'Waiting to start...';
                    }
                });
                
                updateOverallProgress(0);
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
