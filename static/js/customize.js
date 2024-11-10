import { ReactFlow, Controls, Background } from '@reactflow/core';
import '@reactflow/core/dist/style.css';

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('node-editor');
    const paragraphNodesContainer = document.getElementById('paragraph-nodes');
    
    if (!container || !paragraphNodesContainer) {
        console.error('Required containers not found');
        return;
    }

    // Parse story data and initialize style data storage
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

        // Initialize ReactFlow
        const nodes = storyData.paragraphs.map((paragraph, index) => ({
            id: `paragraph-${index}`,
            type: 'paragraphNode',
            position: { x: 250 * (index % 3), y: 300 * Math.floor(index / 3) },
            data: {
                text: paragraph.text,
                index: index,
                image_style: paragraph.image_style || 'realistic'
            }
        }));

        // Initialize style data
        window.styleData = {
            paragraphs: storyData.paragraphs.map((paragraph, index) => ({
                index,
                image_style: paragraph.image_style || 'realistic'
            }))
        };

        // Custom Node Component
        const ParagraphNode = ({ data }) => {
            return `
                <div class="paragraph-node">
                    <div class="node-header">Paragraph ${data.index + 1}</div>
                    <div class="node-content">${data.text.substring(0, 100)}...</div>
                    <div class="node-controls">
                        <select class="node-select" data-type="image_style" data-index="${data.index}">
                            <option value="realistic" ${data.image_style === 'realistic' ? 'selected' : ''}>Realistic</option>
                            <option value="artistic" ${data.image_style === 'artistic' ? 'selected' : ''}>Artistic</option>
                            <option value="fantasy" ${data.image_style === 'fantasy' ? 'selected' : ''}>Fantasy</option>
                        </select>
                    </div>
                </div>
            `;
        };

        // Initialize ReactFlow
        const reactFlow = new ReactFlow({
            container: paragraphNodesContainer,
            nodes: nodes,
            nodeTypes: {
                paragraphNode: ParagraphNode
            },
            defaultViewport: { x: 0, y: 0, zoom: 1 },
            minZoom: 0.5,
            maxZoom: 2,
            snapToGrid: true,
            snapGrid: [20, 20],
            onNodeDragStop: (event, node) => {
                console.log('Node position updated:', node);
            },
            onConnect: (params) => {
                console.log('Connection created:', params);
            }
        });

        // Add background and controls
        reactFlow.addChild(new Background());
        reactFlow.addChild(new Controls());

        // Add event listeners to selects
        document.querySelectorAll('.node-select').forEach(select => {
            select.addEventListener('change', (e) => {
                const index = parseInt(e.target.dataset.index);
                const type = e.target.dataset.type;
                
                // Update style data
                if (!window.styleData.paragraphs[index]) {
                    window.styleData.paragraphs[index] = {
                        index,
                        image_style: 'realistic'
                    };
                }
                
                window.styleData.paragraphs[index] = {
                    ...window.styleData.paragraphs[index],
                    [type]: e.target.value
                };
                
                console.log('Style updated:', window.styleData);
            });
        });

    } catch (error) {
        console.error('Failed to initialize node editor:', error);
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

                // Remove any null values from paragraphs array
                window.styleData.paragraphs = window.styleData.paragraphs.filter(p => p !== null);

                const response = await fetch('/story/update_style', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(window.styleData)
                });

                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to save customization');
                }

                if (data.success) {
                    window.location.href = '/story/generate';
                } else {
                    throw new Error(data.error || 'Server returned unsuccessful response');
                }
            } catch (error) {
                console.error('Error saving customization:', error);
                alert(error.message || 'Failed to save customization');
            } finally {
                saveButton.disabled = false;
                saveButton.innerHTML = 'Generate Cards';
            }
        });
    }
});
