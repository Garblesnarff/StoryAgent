document.addEventListener('DOMContentLoaded', () => {
    // Wait for ReactFlow to be available
    const checkReactFlow = setInterval(() => {
        if (window.ReactFlow) {
            clearInterval(checkReactFlow);
            initializeEditor();
        }
    }, 100);

    function initializeEditor() {
        const container = document.getElementById('node-editor');
        if (!container) return;

        try {
            // Parse story data
            const storyData = JSON.parse(container.dataset.story);
            if (!storyData || !storyData.paragraphs) {
                throw new Error('Invalid story data format');
            }

            const nodes = [];
            const edges = [];

            // Create nodes for each paragraph
            storyData.paragraphs.forEach((paragraph, index) => {
                // Add paragraph node
                nodes.push({
                    id: `p${index}`,
                    type: 'default',
                    position: { x: 100, y: index * 200 },
                    data: {
                        label: React.createElement('div', { className: 'paragraph-node' },
                            React.createElement('div', { className: 'node-header' },
                                `Paragraph ${index + 1}`
                            ),
                            React.createElement('div', { className: 'node-content' },
                                paragraph.text.substring(0, 100) + '...'
                            )
                        )
                    }
                });

                // Add style node
                nodes.push({
                    id: `style${index}`,
                    type: 'default',
                    position: { x: 400, y: index * 200 },
                    data: {
                        label: React.createElement('div', { className: 'effect-node' },
                            React.createElement('div', { className: 'node-header' }, 'Style Options'),
                            React.createElement('select', {
                                className: 'node-select',
                                defaultValue: 'realistic',
                                onChange: (e) => {
                                    window.styleData = window.styleData || { paragraphs: [] };
                                    window.styleData.paragraphs[index] = window.styleData.paragraphs[index] || { index };
                                    window.styleData.paragraphs[index].image_style = e.target.value;
                                }
                            }, [
                                React.createElement('option', { value: 'realistic' }, 'Realistic'),
                                React.createElement('option', { value: 'artistic' }, 'Artistic'),
                                React.createElement('option', { value: 'fantasy' }, 'Fantasy')
                            ])
                        )
                    }
                });

                // Add edge
                edges.push({
                    id: `e${index}`,
                    source: `p${index}`,
                    target: `style${index}`,
                    type: 'smoothstep',
                    animated: true
                });
            });

            // Create root element
            const root = document.createElement('div');
            root.style.width = '100%';
            root.style.height = '100%';
            container.appendChild(root);

            // Create flow component
            const Flow = () => {
                return React.createElement(window.ReactFlow.ReactFlowProvider, null,
                    React.createElement(window.ReactFlow.ReactFlow, {
                        nodes: nodes,
                        edges: edges,
                        fitView: true,
                        nodesDraggable: true,
                        nodesConnectable: false
                    },
                    React.createElement(window.ReactFlow.Background, {
                        color: '#aaa',
                        gap: 16,
                        size: 1
                    }),
                    React.createElement(window.ReactFlow.Controls))
                );
            };

            // Mount the component
            ReactDOM.render(
                React.createElement(Flow),
                root
            );

            // Setup save functionality
            const saveButton = document.getElementById('save-customization');
            if (saveButton) {
                saveButton.addEventListener('click', async () => {
                    try {
                        saveButton.disabled = true;
                        saveButton.textContent = 'Saving...';

                        const response = await fetch('/story/update_style', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(window.styleData || { paragraphs: [] })
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
                        saveButton.textContent = 'Generate Cards';
                    }
                });
            }
        } catch (error) {
            console.error('Failed to initialize node editor:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    <h4 class="alert-heading">Failed to initialize node editor</h4>
                    <p>${error.message}</p>
                    <hr>
                    <p class="mb-0">Please try refreshing the page. If the problem persists, contact support.</p>
                </div>
            `;
        }
    }
});
