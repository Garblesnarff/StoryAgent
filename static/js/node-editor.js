import React, { useState, useCallback, useRef } from 'react';
import ReactFlow, { 
    Controls, 
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    Handle,
    Position,
    getConnectedEdges
} from 'reactflow';
import 'reactflow/dist/style.css';

const ParagraphNode = React.memo(({ data }) => {
    const [isDragOver, setIsDragOver] = useState(false);

    const handleDragOver = (event) => {
        event.preventDefault();
        setIsDragOver(true);
    };

    const handleDragLeave = () => {
        setIsDragOver(false);
    };

    const handleDrop = (event) => {
        event.preventDefault();
        setIsDragOver(false);
        const effectType = event.dataTransfer.getData('effect-type');
        if (effectType && data.onEffectDrop) {
            data.onEffectDrop(data.index, effectType);
        }
    };

    return (
        <div 
            className={`paragraph-node ${data.globalStyle || 'realistic'}-style ${isDragOver ? 'drop-target' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
        >
            <Handle type="target" position={Position.Left} />
            <div className="node-header">Paragraph {data.index + 1}</div>
            <div className="node-content">{data.text}</div>
            <div className="node-controls">
                <button 
                    className="btn btn-primary btn-sm w-100" 
                    onClick={() => data.onGenerateCard(data.index)}
                    disabled={data.isGenerating}>
                    {data.isGenerating ? 'Generating...' : 'Generate Card'}
                </button>
                {data.imageUrl && (
                    <div className="node-preview mt-2">
                        <div className="image-container position-relative">
                            <img 
                                src={data.imageUrl} 
                                alt="Generated preview" 
                                className="img-fluid rounded"
                            />
                            <div className="image-prompt-overlay">
                                {data.imagePrompt}
                            </div>
                        </div>
                    </div>
                )}
                {data.audioUrl && (
                    <div className="audio-player mt-2">
                        <audio 
                            controls 
                            className="w-100"
                            key={data.audioUrl}
                        >
                            <source src={data.audioUrl} type="audio/wav" />
                            Your browser does not support the audio element.
                        </audio>
                    </div>
                )}
            </div>
            <Handle type="source" position={Position.Right} />
        </div>
    );
});

const EffectNode = React.memo(({ data }) => {
    return (
        <div className="effect-node">
            <Handle type="target" position={Position.Left} />
            <div className="node-header">{data.label}</div>
            <div className="node-controls">
                <select 
                    className="form-select"
                    value={data.effect}
                    onChange={(e) => data.onEffectChange(data.id, e.target.value)}>
                    {data.options.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                </select>
            </div>
            <Handle type="source" position={Position.Right} />
        </div>
    );
});

const nodeTypes = {
    paragraph: ParagraphNode,
    effect: EffectNode
};

const EFFECT_OPTIONS = {
    image: [
        { value: 'realistic', label: 'Realistic' },
        { value: 'artistic', label: 'Artistic' },
        { value: 'fantasy', label: 'Fantasy' }
    ],
    mood: [
        { value: 'neutral', label: 'Neutral' },
        { value: 'happy', label: 'Happy' },
        { value: 'sad', label: 'Sad' },
        { value: 'dramatic', label: 'Dramatic' }
    ],
    voice: [
        { value: 'natural', label: 'Natural' },
        { value: 'dramatic', label: 'Dramatic' },
        { value: 'soft', label: 'Soft' },
        { value: 'energetic', label: 'Energetic' }
    ],
    text: [
        { value: 'normal', label: 'Normal' },
        { value: 'poetic', label: 'Poetic' },
        { value: 'descriptive', label: 'Descriptive' },
        { value: 'concise', label: 'Concise' }
    ]
};

const NodeEditor = ({ story, onStyleUpdate }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [selectedStyle, setSelectedStyle] = useState('realistic');
    const reactFlowWrapper = useRef(null);

    const handleEffectDrop = useCallback((paragraphIndex, effectType) => {
        const newNodeId = `effect-${effectType}-${Date.now()}`;
        const paragraphNode = nodes.find(n => n.id === `p${paragraphIndex}`);
        
        if (!paragraphNode) return;

        const newNode = {
            id: newNodeId,
            type: 'effect',
            position: {
                x: paragraphNode.position.x + 300,
                y: paragraphNode.position.y
            },
            data: {
                id: newNodeId,
                label: `${effectType.charAt(0).toUpperCase() + effectType.slice(1)} Effect`,
                effect: EFFECT_OPTIONS[effectType][0].value,
                options: EFFECT_OPTIONS[effectType],
                onEffectChange: handleEffectChange
            }
        };

        const newEdge = {
            id: `e-${paragraphNode.id}-${newNodeId}`,
            source: paragraphNode.id,
            target: newNodeId,
            type: 'smoothstep',
            animated: true
        };

        setNodes(nodes => [...nodes, newNode]);
        setEdges(edges => [...edges, newEdge]);
    }, [nodes, setNodes, setEdges]);

    const handleEffectChange = useCallback((effectNodeId, value) => {
        setNodes(nodes => 
            nodes.map(node => 
                node.id === effectNodeId 
                    ? { ...node, data: { ...node.data, effect: value } }
                    : node
            )
        );
    }, [setNodes]);

    const handleGenerateCard = useCallback(async (index) => {
        if (!story?.paragraphs?.[index]?.text) {
            console.error('No text found for paragraph');
            return;
        }

        try {
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: true}} : node
            ));

            const response = await fetch('/story/generate_cards', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    index: index,
                    text: story.paragraphs[index].text.trim(),
                    style: selectedStyle
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
                            setNodes(currentNodes => {
                                return currentNodes.map(node => 
                                    node.id === `p${index}` ? {
                                        ...node, 
                                        data: {
                                            ...node.data,
                                            imageUrl: data.data.image_url,
                                            imagePrompt: data.data.image_prompt,
                                            audioUrl: data.data.audio_url,
                                            isGenerating: false
                                        }
                                    } : node
                                );
                            });
                        } else if (data.type === 'error') {
                            throw new Error(data.message);
                        }
                    } catch (parseError) {
                        console.error('Error parsing JSON:', parseError);
                    }
                }
            }
        } catch (error) {
            console.error('Error generating card:', error);
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: false}} : node
            ));
            alert(error.message || 'Failed to generate card');
        }
    }, [story?.paragraphs, selectedStyle, setNodes]);

    const handleStyleChange = useCallback((event) => {
        const newStyle = event.target.value;
        setSelectedStyle(newStyle);
        
        setNodes(currentNodes => currentNodes.map(node => ({
            ...node,
            data: {
                ...node.data,
                globalStyle: newStyle
            }
        })));
        
        const updatedParagraphs = story?.paragraphs?.map(p => ({
            ...p,
            image_style: newStyle
        })) || [];
        
        onStyleUpdate(updatedParagraphs);
    }, [setNodes, story?.paragraphs, onStyleUpdate]);

    React.useEffect(() => {
        if (!story?.paragraphs) {
            console.error('No story paragraphs found');
            return;
        }

        const paragraphNodes = story.paragraphs.map((para, index) => ({
            id: `p${index}`,
            type: 'paragraph',
            position: { 
                x: (index % 2) * 300 + 50,
                y: Math.floor(index / 2) * 250 + 50
            },
            sourcePosition: 'right',
            targetPosition: 'left',
            connectable: true,
            data: {
                index,
                text: para.text,
                globalStyle: selectedStyle,
                imageUrl: para.image_url,
                imagePrompt: para.image_prompt,
                audioUrl: para.audio_url,
                onGenerateCard: handleGenerateCard,
                onEffectDrop: handleEffectDrop,
                isGenerating: false
            }
        }));

        setNodes(paragraphNodes);
    }, [story?.paragraphs, selectedStyle, handleGenerateCard, handleEffectDrop, setNodes]);

    React.useEffect(() => {
        const radioButtons = document.querySelectorAll('input[name="imageStyle"]');
        const handler = (e) => handleStyleChange(e);
        
        radioButtons.forEach(radio => {
            radio.addEventListener('change', handler);
        });

        return () => {
            radioButtons.forEach(radio => {
                radio.removeEventListener('change', handler);
            });
        };
    }, [handleStyleChange]);

    React.useEffect(() => {
        // Initialize drag-and-drop for effect items
        const effectItems = document.querySelectorAll('.effect-item');
        
        effectItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('effect-type', item.dataset.effectType);
                item.classList.add('dragging');
            });

            item.addEventListener('dragend', () => {
                item.classList.remove('dragging');
            });
        });
    }, []);

    const onConnect = useCallback((params) => {
        if (params.source === params.target) {
            return;
        }
        
        const edge = {
            ...params,
            type: 'smoothstep',
            animated: true,
            style: { 
                stroke: 'var(--bs-primary)', 
                strokeWidth: 2,
            }
        };
        
        setEdges(currentEdges => addEdge(edge, currentEdges));
    }, [setEdges]);

    return (
        <div ref={reactFlowWrapper} style={{ width: '100%', height: '600px' }} className="node-editor-root">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                nodeTypes={nodeTypes}
                fitView
                style={{ background: 'var(--bs-dark)' }}
                minZoom={0.1}
                maxZoom={4}
                defaultViewport={{ x: 0, y: 0, zoom: 1 }}
                connectOnClick={true}
            >
                <Background />
                <Controls />
            </ReactFlow>
        </div>
    );
};

export default React.memo(NodeEditor);
