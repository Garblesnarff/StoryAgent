document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');
    const uploadForm = document.getElementById('upload-form');
    
    if (!storyForm && !uploadForm) {
        console.error('Error: Required form elements not found');
        return;
    }

    // Helper function to show error messages
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show mt-3';
        errorDiv.innerHTML = `
            <strong>Error:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        const form = document.querySelector('form');
        const existingError = form.parentElement.querySelector('.alert');
        if (existingError) {
            existingError.remove();
        }
        form.parentElement.insertBefore(errorDiv, form.nextSibling);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            errorDiv.classList.remove('show');
            setTimeout(() => errorDiv.remove(), 150);
        }, 5000);
    }

    // Add easing function for smoother animation
    function easeInOutCubic(x) {
        return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
    }

    // Add smooth progress animation function
    function animateProgress(progressBar, start, end) {
        const duration = 800;
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

    if (storyForm) {
        storyForm.addEventListener('submit', async (e) => {
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
                    showError('Server returned an invalid response. Please try again.');
                    return;
                }
                
                if (!response.ok) {
                    if (response.status === 429) {
                        showError('Too many requests. Please wait a moment before trying again.');
                    } else if (response.status === 413) {
                        showError('File size too large. Please try a smaller file.');
                    } else {
                        showError(data.error || 'Story generation failed. Please try again.');
                    }
                    return;
                }

                if (data.success && data.redirect) {
                    window.location.href = data.redirect;
                } else {
                    showError(data.error || 'Invalid response from server. Please try again.');
                }
            } catch (error) {
                console.error('Error:', error);
                const errorMessage = error.response?.status === 429 
                    ? 'Too many requests. Please wait a moment before trying again.'
                    : error.response?.status === 400
                        ? 'Invalid input. Please check your story parameters.'
                        : error.message || 'An unexpected error occurred. Please try again.';
                showError(errorMessage);
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }
        });
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
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
                let errorMessage = 'An unexpected error occurred. Please try again.';
                
                if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                    errorMessage = 'Network error. Please check your connection and try again.';
                } else if (error.response?.status === 413) {
                    errorMessage = 'File size too large. Please try a smaller file.';
                } else if (error.response?.status === 415) {
                    errorMessage = 'Unsupported file type. Please upload PDF, EPUB, or HTML files only.';
                } else if (error.message) {
                    errorMessage = error.message;
                }
                
                uploadStatus.innerHTML = `<span class="text-danger"><strong>Error:</strong> ${errorMessage}</span>`;
                progressBar.style.width = '0%';
                progressBar.style.transition = 'none';
            } finally {
                submitButton.disabled = false;
                spinner.classList.add('d-none');
            }
        });
    }
});
