// Initialize React Flow
const nodeTypes = {
    paragraph: ParagraphNode,
    effect: EffectNode
};

function ParagraphNode({ data }) {
    return (
        <div className="paragraph-node">
            <div className="node-header">Paragraph {data.index + 1}</div>
            <div className="node-content">{data.text.substring(0, 100)}...</div>
        </div>
    );
}

function EffectNode({ data }) {
    return (
        <div className="effect-node">
            <div className="node-header">{data.type}</div>
            <select className="node-select" onChange={data.onChange}>
                {data.options.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
            </select>
        </div>
    );
}

function handleStyleChange(index, styleType, value) {
    const styleData = window.styleData || { paragraphs: [] };
    if (!styleData.paragraphs[index]) {
        styleData.paragraphs[index] = { index };
    }
    styleData.paragraphs[index][styleType] = value;
    window.styleData = styleData;
}

function NodeEditor({ paragraphs }) {
    const [nodes, setNodes] = React.useState([]);
    const [edges, setEdges] = React.useState([]);

    React.useEffect(() => {
        // Create paragraph nodes
        const paragraphNodes = paragraphs.map((p, i) => ({
            id: `p-${i}`,
            type: 'paragraph',
            position: { x: 100, y: i * 200 },
            data: { index: i, text: p.text }
        }));

        // Create effect nodes
        const effectNodes = paragraphs.map((p, i) => {
            return [
                {
                    id: `img-${i}`,
                    type: 'effect',
                    position: { x: 400, y: i * 200 },
                    data: {
                        type: 'Image Style',
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
                        options: [
                            { value: 'neutral', label: 'Neutral' },
                            { value: 'dramatic', label: 'Dramatic' },
                            { value: 'emotional', label: 'Emotional' }
                        ],
                        onChange: (e) => handleStyleChange(i, 'voice_style', e.target.value)
                    }
                }
            ];
        }).flat();

        // Create edges
        const edges = paragraphs.map((p, i) => [
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
        ]).flat();

        setNodes([...paragraphNodes, ...effectNodes]);
        setEdges(edges);
    }, [paragraphs]);

    return (
        <div style={{ width: '100%', height: '400px' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                fitView
            />
        </div>
    );
}

// Initialize the editor when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('node-editor');
    const storyData = JSON.parse(container.dataset.story);
    
    ReactDOM.render(
        <NodeEditor paragraphs={storyData.paragraphs} />,
        container
    );
    
    // Handle save and generation
    const saveButton = document.getElementById('save-customization');
    saveButton?.addEventListener('click', async () => {
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
});
