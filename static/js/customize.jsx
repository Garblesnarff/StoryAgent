import React from 'react';
import ReactDOM from 'react-dom/client';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';

const ParagraphNode = ({ data }) => {
    return (
        <div className="paragraph-node">
            <div className="node-header">Paragraph {data.index + 1}</div>
            <div className="node-content">{data.text.substring(0, 100)}...</div>
            <div className="node-controls">
                <select 
                    className="node-select" 
                    value={data.image_style}
                    onChange={(e) => data.updateStyle(data.index, 'image_style', e.target.value)}
                >
                    <option value="realistic">Realistic</option>
                    <option value="artistic">Artistic</option>
                    <option value="fantasy">Fantasy</option>
                </select>
            </div>
        </div>
    );
};

const StoryFlow = ({ storyData }) => {
    const nodeTypes = {
        paragraphNode: ParagraphNode
    };

    const updateStyle = (index, type, value) => {
        if (!window.styleData.paragraphs[index]) {
            window.styleData.paragraphs[index] = {
                index,
                image_style: 'realistic',
                text: storyData.paragraphs[index].text
            };
        }
        
        window.styleData.paragraphs[index] = {
            ...window.styleData.paragraphs[index],
            [type]: value
        };
        
        console.log('Style updated:', window.styleData);
    };

    const nodes = storyData.paragraphs.map((paragraph, index) => ({
        id: `paragraph-${index}`,
        type: 'paragraphNode',
        position: { x: 250 * index, y: 100 },
        data: {
            text: paragraph.text,
            index: index,
            image_style: paragraph.image_style || 'realistic',
            updateStyle
        }
    }));

    const edges = nodes.slice(1).map((node, index) => ({
        id: `edge-${index}`,
        source: `paragraph-${index}`,
        target: node.id,
        type: 'smoothstep'
    }));

    return (
        <div style={{ width: '100%', height: '600px' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                fitView
                minZoom={0.5}
                maxZoom={2}
            >
                <Background />
                <Controls />
                <MiniMap />
            </ReactFlow>
        </div>
    );
};

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('node-editor');
    
    if (!container) {
        console.error('Required container not found');
        return;
    }

    try {
        const rawData = container.dataset.story;
        if (!rawData) {
            throw new Error('No story data found');
        }
        const storyData = JSON.parse(rawData);
        if (!storyData || !Array.isArray(storyData.paragraphs)) {
            throw new Error('Invalid story data format: Expected array of paragraphs');
        }

        // Initialize style data
        window.styleData = {
            paragraphs: storyData.paragraphs.map((paragraph, index) => ({
                index,
                image_style: paragraph.image_style || 'realistic',
                text: paragraph.text
            }))
        };

        // Create React root and render
        const root = ReactDOM.createRoot(container);
        root.render(<StoryFlow storyData={storyData} />);

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

    } catch (error) {
        console.error('Failed to initialize ReactFlow:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <h4 class="alert-heading">Failed to load story data</h4>
                <p>${error.message}</p>
                <hr>
                <p class="mb-0">Please make sure you have a valid story selected.</p>
            </div>
        `;
    }
});
