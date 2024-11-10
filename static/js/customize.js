document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('node-editor');
    const paragraphNodesContainer = document.getElementById('paragraph-nodes');
    
    if (!container || !paragraphNodesContainer) {
        console.error('Required containers not found');
        return;
    }

    // Initialize style data storage
    window.styleData = { paragraphs: [] };

    // Parse story data
    let storyData;
    try {
        const rawData = container.dataset.story;
        if (!rawData) {
            throw new Error('No story data found');
        }
        storyData = JSON.parse(rawData);
        if (!storyData || !Array.isArray(storyData.paragraphs)) {
            throw new Error('Invalid story data format: Expected array of paragraphs');
        }
    } catch (error) {
        console.error('Failed to parse story data:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <h4 class="alert-heading">Failed to load story data</h4>
                <p>${error.message}</p>
                <hr>
                <p class="mb-0">Please make sure you have a valid story selected.</p>
            </div>
        `;
        return;
    }

    // Create paragraph nodes
    const paragraphNodes = storyData.paragraphs.map((paragraph, index) => {
        const card = document.createElement('div');
        card.className = 'card paragraph-node';
        card.innerHTML = `
            <div class="card-body">
                <div class="node-header">Paragraph ${index + 1}</div>
                <div class="node-content">${paragraph.text.substring(0, 100)}...</div>
                <div class="node-controls">
                    <select class="node-select" data-type="image-style" data-index="${index}">
                        <option value="realistic" ${paragraph.image_style === 'realistic' ? 'selected' : ''}>Realistic</option>
                        <option value="artistic" ${paragraph.image_style === 'artistic' ? 'selected' : ''}>Artistic</option>
                        <option value="fantasy" ${paragraph.image_style === 'fantasy' ? 'selected' : ''}>Fantasy</option>
                    </select>
                    <select class="node-select" data-type="voice-style" data-index="${index}">
                        <option value="neutral" ${paragraph.voice_style === 'neutral' ? 'selected' : ''}>Neutral</option>
                        <option value="dramatic" ${paragraph.voice_style === 'dramatic' ? 'selected' : ''}>Dramatic</option>
                        <option value="cheerful" ${paragraph.voice_style === 'cheerful' ? 'selected' : ''}>Cheerful</option>
                    </select>
                </div>
            </div>
        `;

        // Add event listeners to selects
        const selects = card.querySelectorAll('.node-select');
        selects.forEach(select => {
            select.addEventListener('change', (e) => {
                const index = parseInt(e.target.dataset.index);
                const type = e.target.dataset.type;
                
                window.styleData.paragraphs[index] = window.styleData.paragraphs[index] || { index };
                window.styleData.paragraphs[index][type] = e.target.value;
                
                console.log('Style updated:', window.styleData);
            });
        });

        return card;
    });

    // Add nodes to container
    paragraphNodesContainer.append(...paragraphNodes);

    // Setup save functionality
    const saveButton = document.getElementById('save-customization');
    if (saveButton) {
        saveButton.addEventListener('click', async () => {
            try {
                saveButton.disabled = true;
                saveButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Saving...';

                if (!window.styleData?.paragraphs?.length) {
                    throw new Error('No style changes to save');
                }

                const response = await fetch('/story/update_style', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(window.styleData)
                });

                if (!response.ok) {
                    throw new Error('Failed to save customization');
                }

                const data = await response.json();
                if (data.success) {
                    window.location.href = '/story/generate';
                } else {
                    throw new Error(data.error || 'Failed to save customization');
                }
            } catch (error) {
                console.error('Error:', error);
                alert(error.message);
            } finally {
                saveButton.disabled = false;
                saveButton.innerHTML = 'Generate Cards';
            }
        });
    }
});
