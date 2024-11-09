document.addEventListener('DOMContentLoaded', () => {
    // Wait for ReactFlow to be fully loaded
    const initializeEditor = () => {
        try {
            const container = document.getElementById('node-editor');
            if (!container) {
                console.error('Node editor container not found');
                return;
            }

            const storyData = JSON.parse(container.dataset.story);
            
            // Create root element
            const root = document.createElement('div');
            root.style.width = '100%';
            root.style.height = '100%';
            container.appendChild(root);

            // Verify ReactFlow is loaded
            if (!window.ReactFlow) {
                throw new Error('ReactFlow not loaded');
            }

            // Node components
            const ParagraphNode = ({ data }) => {
                return React.createElement('div',
                    { className: 'paragraph-node' },
                    React.createElement('div',
                        { className: 'node-header' },
                        `Paragraph ${data.index + 1}`
                    ),
                    React.createElement('div',
                        { className: 'node-content' },
                        data.text.substring(0, 100) + '...'
                    )
                );
            };

            const EffectNode = ({ data }) => {
                return React.createElement('div',
                    { className: 'effect-node' },
                    React.createElement('div',
                        { className: 'node-header' },
                        data.type
                    ),
                    React.createElement('select',
                        {
                            className: 'node-select',
                            onChange: data.onChange,
                            defaultValue: data.defaultValue
                        },
                        data.options.map(opt =>
                            React.createElement('option',
                                {
                                    key: opt.value,
                                    value: opt.value
                                },
                                opt.label
                            )
                        )
                    )
                );
            };

            // Style change handler
            const handleStyleChange = (index, styleType, value) => {
                window.styleData = window.styleData || { paragraphs: [] };
                if (!window.styleData.paragraphs[index]) {
                    window.styleData.paragraphs[index] = { index };
                }
                window.styleData.paragraphs[index][styleType] = value;
            };

            // Create nodes
            const paragraphNodes = storyData.paragraphs.map((p, i) => ({
                id: `p-${i}`,
                type: 'paragraph',
                position: { x: 100, y: i * 200 },
                data: { index: i, text: p.text }
            }));

            const effectNodes = storyData.paragraphs.flatMap((p, i) => [
                {
                    id: `img-${i}`,
                    type: 'effect',
                    position: { x: 400, y: i * 200 },
                    data: {
                        type: 'Image Style',
                        defaultValue: 'realistic',
                        options: [
                            { value: 'realistic', label: 'Realistic' },
                            { value: 'artistic', label: 'Artistic' },
                            { value: 'fantasy', label: 'Fantasy' }
                        ],
                        onChange: (e) => handleStyleChange(i, 'image_style', e.target.value)
                    }
                },
                {
                    id: `voice-${i}`,
                    type: 'effect',
                    position: { x: 600, y: i * 200 },
                    data: {
                        type: 'Voice Style',
                        defaultValue: 'neutral',
                        options: [
                            { value: 'neutral', label: 'Neutral' },
                            { value: 'dramatic', label: 'Dramatic' },
                            { value: 'emotional', label: 'Emotional' }
                        ],
                        onChange: (e) => handleStyleChange(i, 'voice_style', e.target.value)
                    }
                }
            ]);

            const edges = storyData.paragraphs.flatMap((p, i) => [
                {
                    id: `p${i}-img${i}`,
                    source: `p-${i}`,
                    target: `img-${i}`,
                    type: 'smoothstep'
                },
                {
                    id: `p${i}-voice${i}`,
                    source: `p-${i}`,
                    target: `voice-${i}`,
                    type: 'smoothstep'
                }
            ]);

            // Create flow component using window.ReactFlow directly
            const Flow = () => {
                const nodeTypes = {
                    paragraph: ParagraphNode,
                    effect: EffectNode
                };

                return React.createElement(window.ReactFlow.ReactFlowProvider, null,
                    React.createElement(window.ReactFlow.ReactFlow, {
                        nodes: [...paragraphNodes, ...effectNodes],
                        edges: edges,
                        nodeTypes: nodeTypes,
                        fitView: true,
                        minZoom: 0.5,
                        maxZoom: 1.5,
                        nodesDraggable: true,
                        nodesConnectable: false,
                        elementsSelectable: true
                    },
                    React.createElement(window.ReactFlow.Background, {
                        color: '#aaa',
                        gap: 16,
                        size: 1
                    }),
                    React.createElement(window.ReactFlow.Controls))
                );
            };

            // Render the editor
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
                        const response = await fetch('/story/update_style', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(window.styleData || { paragraphs: [] })
                        });
                        
                        if (!response.ok) {
                            throw new Error('Failed to save style customization');
                        }
                        
                        const data = await response.json();
                        if (data.success) {
                            window.location.href = '/story/generate';
                        } else {
                            throw new Error(data.error || 'Failed to save customization');
                        }
                        
                    } catch (error) {
                        console.error('Error:', error);
                        alert('Failed to save customization. Please try again.');
                    } finally {
                        saveButton.disabled = false;
                    }
                });
            }

        } catch (error) {
            console.error('Failed to initialize node editor:', error);
            const container = document.getElementById('node-editor');
            if (container) {
                container.innerHTML = `<div class="alert alert-danger">Failed to initialize node editor. Please try refreshing the page.</div>`;
            }
        }
    };

    // Try to initialize with delay to ensure scripts are loaded
    setTimeout(initializeEditor, 1000);
});
