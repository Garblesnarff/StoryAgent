// customize.js
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('node-editor');
    const storyData = JSON.parse(container.dataset.story);
    
    // Create root element for React
    const root = document.createElement('div');
    root.style.width = '100%';
    root.style.height = '100%';
    container.appendChild(root);
    
    // Initialize ReactFlow
    const ReactFlowProvider = ReactFlow.ReactFlowProvider;
    const ReactFlowInstance = ReactFlow.ReactFlow;
    
    // Define node components
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

    // Create main editor component
    const NodeEditor = () => {
        const [nodes, setNodes] = React.useState([]);
        const [edges, setEdges] = React.useState([]);
        
        React.useEffect(() => {
            // Create paragraph nodes
            const paragraphNodes = storyData.paragraphs.map((p, i) => ({
                id: `p-${i}`,
                type: 'paragraph',
                position: { x: 100, y: i * 200 },
                data: { index: i, text: p.text }
            }));

            // Create effect nodes
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

        const handleStyleChange = (index, styleType, value) => {
            window.styleData = window.styleData || { paragraphs: [] };
            if (!window.styleData.paragraphs[index]) {
                window.styleData.paragraphs[index] = { index };
            }
            window.styleData.paragraphs[index][styleType] = value;
        };

        return React.createElement(ReactFlowInstance, {
            nodes: nodes,
            edges: edges,
            nodeTypes: {
                paragraph: ParagraphNode,
                effect: EffectNode
            },
            fitView: true,
            minZoom: 0.5,
            maxZoom: 1.5,
            nodesDraggable: true,
            nodesConnectable: false,
            elementsSelectable: true
        });
    };

    // Render editor with ReactFlow provider
    ReactDOM.render(
        React.createElement(ReactFlowProvider, null,
            React.createElement(NodeEditor)
        ),
        root
    );
    
    // Handle save and generation
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
});
