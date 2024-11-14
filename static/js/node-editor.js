import React, { useState, useCallback } from 'react';
import ReactFlow, { 
    Controls, 
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
} from 'reactflow';
import 'reactflow/dist/style.css';

const nodeTypes = {
    paragraph: ParagraphNode,
    effect: EffectNode
};

function ParagraphNode({ data }) {
    return (
        <div className={`paragraph-node ${data.imageStyle || 'realistic'}-style`}>
            <div className="node-header">Paragraph {data.index + 1}</div>
            <div className="node-content">{data.text.substring(0, 100)}...</div>
            <div className="node-controls">
                <div className="node-select-group">
                    <label className="node-select-label">Image Style</label>
                    <select 
                        className="node-select"
                        value={data.imageStyle}
                        onChange={(e) => {
                            console.log('Style changed:', {type: 'image', value: e.target.value, index: data.index});
                            data.onStyleChange('image', e.target.value);
                        }}>
                        <option value="realistic">Realistic</option>
                        <option value="artistic">Artistic</option>
                        <option value="fantasy">Fantasy</option>
                    </select>
                </div>
                <button 
                    className="btn btn-primary btn-sm w-100 mt-2" 
                    onClick={() => data.onGenerateCard(data.index)}
                    disabled={data.isGenerating}>
                    {data.isGenerating ? 'Generating...' : 'Generate Card'}
                </button>
                {data.imageUrl && (
                    <div className="node-preview mt-2">
                        <img src={data.imageUrl} alt="Generated preview" className="img-fluid rounded" />
                    </div>
                )}
            </div>
        </div>
    );
}

function EffectNode({ data }) {
    return (
        <div className="effect-node">
            <div className="node-header">{data.label}</div>
            <div className="node-controls">
                <select 
                    className="node-select"
                    value={data.effect}
                    onChange={(e) => data.onEffectChange(e.target.value)}>
                    {data.options.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                </select>
            </div>
        </div>
    );
}

function NodeEditor({ story, onStyleUpdate }) {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    const handleGenerateCard = useCallback(async (index) => {
        try {
            // Get the current node data
            const currentNode = nodes.find(n => n.id === `p${index}`);
            if (!currentNode || !currentNode.data || !currentNode.data.text) {
                throw new Error('No text found for paragraph');
            }

            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: true}} : node
            ));

            const response = await fetch('/story/generate_cards', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    index: index,
                    text: currentNode.data.text,
                    style: currentNode.data.imageStyle || 'realistic'
                })
            });

            if (!response.ok) throw new Error('Failed to generate card');
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const {done, value} = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, {stream: true});
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (!line.trim()) continue;
                    
                    try {
                        const data = JSON.parse(line);
                        if (data.type === 'paragraph') {
                            setNodes(nodes => nodes.map(node => 
                                node.id === `p${index}` ? {
                                    ...node, 
                                    data: {
                                        ...node.data,
                                        imageUrl: data.data.image_url,
                                        imagePrompt: data.data.image_prompt,
                                        isGenerating: false
                                    }
                                } : node
                            ));
                        } else if (data.type === 'error') {
                            throw new Error(data.message);
                        }
                    } catch (parseError) {
                        console.error('Error parsing JSON:', parseError);
                        console.debug('Problematic line:', line);
                        continue;
                    }
                }
            }
        } catch (error) {
            console.error('Error generating card:', error);
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: false}} : node
            ));
            alert(error.message || 'Failed to generate card');
        }
    }, [nodes, setNodes]);

    const handleStyleChange = useCallback((index, type, value) => {
        // Update local node state
        setNodes(nodes => nodes.map(node => {
            if (node.id === `p${index}`) {
                return {
                    ...node,
                    data: {
                        ...node.data,
                        imageStyle: value
                    }
                };
            }
            return node;
        }));
        
        // Call parent update handler
        const updatedParagraphs = story.paragraphs.map((p, i) => {
            if (i === index) {
                return {
                    ...p,
                    image_style: value
                };
            }
            return p;
        });
        onStyleUpdate(updatedParagraphs);
    }, [story, onStyleUpdate]);

    React.useEffect(() => {
        if (story?.paragraphs) {
            // Create nodes from paragraphs
            const paragraphNodes = story.paragraphs.map((para, index) => ({
                id: `p${index}`,
                type: 'paragraph',
                position: { x: 250, y: index * 200 },
                data: {
                    index,
                    text: para.text,
                    imageStyle: para.image_style || 'realistic',
                    onStyleChange: (type, value) => handleStyleChange(index, type, value),
                    onGenerateCard: handleGenerateCard,
                    isGenerating: false,
                    imageUrl: para.image_url,
                    audioUrl: para.audio_url
                }
            }));

            setNodes(paragraphNodes);
        }
    }, [story, handleStyleChange, handleGenerateCard]);

    const onConnect = useCallback((params) => 
        setEdges((eds) => addEdge(params, eds)), []);

    return (
        <div style={{ width: '100%', height: '600px' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                nodeTypes={nodeTypes}
                fitView
            >
                <Background />
                <Controls />
            </ReactFlow>
        </div>
    );
}

export default NodeEditor;
