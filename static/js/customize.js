document.addEventListener('DOMContentLoaded', () => {
    // Wait for ReactFlow to be fully loaded
    setTimeout(() => {
        const container = document.getElementById('node-editor');
        const storyData = JSON.parse(container.dataset.story);
        
        // Create root element for React
        const root = document.createElement('div');
        root.style.width = '100%';
        root.style.height = '100%';
        container.appendChild(root);

        // Initialize ReactFlow components
        const ReactFlowProvider = window.ReactFlow.ReactFlowProvider;
        const ReactFlow = window.ReactFlow.default || window.ReactFlow.ReactFlow;
        const Background = window.ReactFlow.Background;
        const Controls = window.ReactFlow.Controls;
        
        // Create node components using React.createElement
        const ParagraphNode = React.memo(function({ data }) {
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
        });

        const EffectNode = React.memo(function({ data }) {
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
        });

        // Create node editor component
        function NodeEditor() {
            const [nodes, setNodes] = React.useState([]);
            const [edges, setEdges] = React.useState([]);
            
            React.useEffect(() => {
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

                setNodes([...paragraphNodes, ...effectNodes]);
                setEdges(storyData.paragraphs.flatMap((p, i) => [
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
                ]));
            }, []);

            return React.createElement(ReactFlowProvider, null,
                React.createElement(ReactFlow, {
                    nodes: nodes,
                    edges: edges,
                    nodeTypes: { paragraph: ParagraphNode, effect: EffectNode },
                    fitView: true,
                    minZoom: 0.5,
                    maxZoom: 1.5,
                    nodesDraggable: true,
                    nodesConnectable: false,
                    elementsSelectable: true
                },
                React.createElement(Background, {
                    color: '#aaa',
                    gap: 16,
                    size: 1
                }),
                React.createElement(Controls))
            );
        }

        // Initialize the editor
        ReactDOM.render(
            React.createElement(NodeEditor),
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
    }, 100); // Small delay to ensure all scripts are loaded
});
