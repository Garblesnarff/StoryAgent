document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');
    const uploadForm = document.getElementById('upload-form');

    // Add easing function for smoother animation
    function easeInOutCubic(x) {
        return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
    }

    // Add smooth progress animation function
    function animateProgress(progressBar, start, end) {
        const duration = 800; // Increased duration
        const startTime = performance.now();
        
        progressBar.style.transition = 'all 0.3s ease';
        progressBar.style.background = 'linear-gradient(45deg, var(--bs-primary) 25%, var(--bs-primary-rgb, 13, 110, 253) 50%, var(--bs-primary) 75%)';
        progressBar.style.backgroundSize = '200% 100%';
        progressBar.style.animation = 'progress-wave 2s linear infinite';
        
        return new Promise(resolve => {
            function update(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                const current = start + (end - start) * easeInOutCubic(progress);
                progressBar.style.width = `${current}%`;
                
                if (progress < 1) {
                    requestAnimationFrame(update);
                } else {
                    resolve();
                }
            }
            requestAnimationFrame(update);
        });
    }

    storyForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Show loading state
        const submitButton = storyForm.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = 'Generating...';
        
        try {
            const formData = new FormData(storyForm);
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
            submitButton.disabled = false;
            submitButton.textContent = originalText;
        }
    });

    uploadForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(uploadForm);
        const submitButton = uploadForm.querySelector('button[type="submit"]');
        const buttonText = submitButton.querySelector('.button-text');
        const spinner = submitButton.querySelector('.spinner-border');
        const progressBar = document.querySelector('#upload-progress .progress-bar');
        const uploadProgress = document.getElementById('upload-progress');
        const uploadStatus = document.getElementById('upload-status');
        
        // Reset and show progress elements
        uploadProgress.classList.remove('d-none');
        progressBar.style.width = '0%';
        uploadStatus.textContent = '';
        submitButton.disabled = true;
        spinner.classList.remove('d-none');
        
        try {
            // Start with upload phase
            uploadStatus.innerHTML = '<strong><span class="phase-icon">📤</span>Phase 1/3:</strong> Uploading file...';
            await animateProgress(progressBar, 0, 33);
            
            const response = await fetch('/story/upload', {
                method: 'POST',
                body: formData
            });
            
            let data;
            try {
                data = await response.json();
            } catch (parseError) {
                throw new Error('Server returned an invalid response');
            }
            
            if (!response.ok) {
                throw new Error(data.error || 'Upload failed');
            }
            
            // Processing phase
            uploadStatus.innerHTML = '<strong><span class="phase-icon">⚙️</span>Phase 2/3:</strong> Processing document...';
            await animateProgress(progressBar, 33, 66);
            await new Promise(resolve => setTimeout(resolve, 800)); // Small delay
            
            // Text extraction phase
            uploadStatus.innerHTML = '<strong><span class="phase-icon">📑</span>Phase 3/3:</strong> Extracting text...';
            await animateProgress(progressBar, 66, 100);
            await new Promise(resolve => setTimeout(resolve, 800)); // Small delay
            
            // Complete
            uploadStatus.innerHTML = '<strong><span class="phase-icon">✨</span>Complete!</strong> Redirecting to editor...';
            
            if (data.redirect) {
                window.location.href = data.redirect;
            }
            
        } catch (error) {
            console.error('Error:', error);
            uploadStatus.innerHTML = `<span class="text-danger"><strong>Error:</strong> ${error.message}</span>`;
            progressBar.style.width = '0%';
        } finally {
            submitButton.disabled = false;
            spinner.classList.add('d-none');
        }
    });
});
