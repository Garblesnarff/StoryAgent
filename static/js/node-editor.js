import React, { useState, useCallback } from 'react';
import ReactFlow, { 
    Controls, 
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
} from 'reactflow';
import 'reactflow/dist/style.css';

export function ParagraphNode({ data }) {
    return (
        <div className={`paragraph-node ${data.globalStyle || 'realistic'}-style`}>
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

const nodeTypes = {
    paragraph: ParagraphNode,
    effect: EffectNode
};

function NodeEditor({ story, onStyleUpdate }) {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [selectedStyle, setSelectedStyle] = useState('realistic');

    // Add immediate initialization of nodes
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
            data: {
                index,
                text: para.text,
                globalStyle: selectedStyle,
                imageUrl: para.image_url,
                imagePrompt: para.image_prompt,
                audioUrl: para.audio_url,
                onGenerateCard: handleGenerateCard,
                isGenerating: false
            }
        }));

        console.log('Initializing nodes:', paragraphNodes);
        setNodes(paragraphNodes);
    }, [story?.paragraphs, selectedStyle, handleGenerateCard]);

    const handleStyleChange = useCallback((event) => {
        const newStyle = event.target.value;
        setSelectedStyle(newStyle);
        
        // Update all nodes with the new global style
        setNodes(nodes => nodes.map(node => ({
            ...node,
            data: {
                ...node.data,
                globalStyle: newStyle
            }
        })));
        
        // Update the parent component
        const updatedParagraphs = story.paragraphs.map(p => ({
            ...p,
            image_style: newStyle
        }));
        
        onStyleUpdate(updatedParagraphs);
    }, [setNodes, story, onStyleUpdate]);

    const handleGenerateCard = useCallback(async (index) => {
        try {
            const paragraphText = story.paragraphs[index]?.text;
            if (!paragraphText) {
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
                    text: paragraphText.trim(),
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
                            setNodes(nodes => {
                                return nodes.map(node => 
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
    }, [nodes, setNodes, story.paragraphs, selectedStyle]);

    React.useEffect(() => {
        // Add event listener for radio buttons
        const radioButtons = document.querySelectorAll('input[name="imageStyle"]');
        radioButtons.forEach(radio => {
            radio.addEventListener('change', handleStyleChange);
        });

        // Cleanup
        return () => {
            radioButtons.forEach(radio => {
                radio.removeEventListener('change', handleStyleChange);
            });
        };
    }, [handleStyleChange]);

    const onConnect = useCallback((params) => 
        setEdges((eds) => addEdge(params, eds)), []);

    return (
        <div style={{ width: '100%', height: '600px', position: 'relative' }} className="node-editor-root">
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
            >
                <Background />
                <Controls />
            </ReactFlow>
        </div>
    );
}

export default NodeEditor;
