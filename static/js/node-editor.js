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
                    onStyleChange: (type, value) => handleStyleChange(index, type, value)
                }
            }));

            setNodes(paragraphNodes);
        }
    }, [story, handleStyleChange]);

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
