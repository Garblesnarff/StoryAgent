import React, { useState, useCallback, useEffect } from 'react';
import ReactFlow, { 
    Node,
    Edge,
    Controls, 
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    Handle,
    Position,
    NodeProps,
    NodeDragHandler,
    Connection,
    XYPosition
} from 'reactflow';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import 'reactflow/dist/style.css';

interface Story {
    paragraphs: Array<{
        text: string;
        image_url?: string;
        image_prompt?: string;
        audio_url?: string;
    }>;
}

interface NodeData {
    index: number;
    text: string;
    globalStyle: string;
    imageUrl?: string;
    imagePrompt?: string;
    audioUrl?: string;
    onGenerateCard: (index: number) => Promise<void>;
    onRegenerateImage: (index: number) => Promise<void>;
    onRegenerateAudio: (index: number) => Promise<void>;
    onExpandImage: (url: string) => void;
    onStyleChange?: (index: number, style: string) => void;
    isGenerating: boolean;
    isRegenerating: boolean;
    isRegeneratingAudio: boolean;
}

interface NodeEditorProps {
    story?: Story;
    onStyleUpdate?: (paragraphs: Array<{ index: number; image_style: string }>) => void;
}

interface SavedNodePosition {
    x: number;
    y: number;
}

type SavedPositions = Record<string, SavedNodePosition>;

interface ParagraphData {
    index: number;
    text: string;
    globalStyle: string;
    imageUrl?: string;
    imagePrompt?: string;
    audioUrl?: string;
    onGenerateCard: (index: number) => void;
    onRegenerateImage: (index: number) => void;
    onRegenerateAudio: (index: number) => void;
    onExpandImage: (url: string) => void;
    onStyleChange?: (index: number, style: string) => void;
    isGenerating: boolean;
    isRegenerating: boolean;
    isRegeneratingAudio: boolean;
}

const ParagraphNode: React.FC<NodeProps<NodeData>> = ({ data }) => {
    const [showPrompt, setShowPrompt] = useState(false);
    const [localStyle, setLocalStyle] = useState(data.globalStyle || 'realistic');

    return (
        <div className={`paragraph-node ${localStyle}-style`}>
            <Handle type="target" position={Position.Left} className="!bg-primary" />
            <div className="text-lg font-bold mb-2 text-primary">Paragraph {data.index + 1}</div>
            <div className="text-sm text-card-foreground mb-4 max-h-[120px] overflow-y-auto">
                {data.text}
            </div>
            <div className="space-y-4">
                <Button 
                    className="w-full"
                    onClick={() => data.onGenerateCard(data.index)}
                    disabled={data.isGenerating}>
                    {data.isGenerating ? (
                        <div className="flex items-center justify-center gap-2">
                            <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                            <span>Generating...</span>
                        </div>
                    ) : 'Generate Card'}
                </Button>
                
                <div className="mt-4 mb-2">
                    <RadioGroup
                        value={localStyle}
                        onValueChange={(value) => {
                            setLocalStyle(value);
                            data.onStyleChange?.(data.index, value);
                        }}
                        className="flex gap-4 justify-center"
                    >
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem value="realistic" id={`realistic-${data.index}`} />
                            <Label htmlFor={`realistic-${data.index}`}>Realistic</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem value="artistic" id={`artistic-${data.index}`} />
                            <Label htmlFor={`artistic-${data.index}`}>Artistic</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem value="fantasy" id={`fantasy-${data.index}`} />
                            <Label htmlFor={`fantasy-${data.index}`}>Fantasy</Label>
                        </div>
                    </RadioGroup>
                </div>
                
                {data.imageUrl && (
                    <>
                        <div className="relative rounded-lg overflow-hidden border border-border">
                            <img 
                                src={data.imageUrl} 
                                alt="Generated preview" 
                                className="w-full h-auto object-cover"
                                onError={(e) => {
                                    console.error('Image failed to load:', data.imageUrl);
                                    e.currentTarget.src = '/static/placeholder.png';
                                }}
                            />
                            {showPrompt && (
                                <div className="absolute inset-0 bg-black/75 p-4 text-white overflow-y-auto transition-all duration-200">
                                    <p className="text-sm">{data.imagePrompt}</p>
                                </div>
                            )}
                        </div>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                className="flex-1"
                                onClick={() => data.onRegenerateImage(data.index)}
                                disabled={data.isRegenerating}
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                                    <path d="M3 3v5h5" />
                                    <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
                                    <path d="M16 16h5v5" />
                                </svg>
                                Regenerate
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setShowPrompt(!showPrompt)}
                            >
                                {showPrompt ? 'Hide Prompt' : 'Show Prompt'}
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => data.onExpandImage(data.imageUrl!)}
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
                                </svg>
                            </Button>
                        </div>
                    </>
                )}
                
                {data.audioUrl && (
                    <>
                        <div className="audio-player mt-4">
                            <audio
                                controls
                                className="w-full"
                                key={data.audioUrl}
                                onError={(e) => console.error('Audio failed to load:', data.audioUrl)}
                            >
                                <source src={data.audioUrl} type="audio/wav" />
                                Your browser does not support the audio element.
                            </audio>
                        </div>
                        <button 
                            className="btn btn-secondary btn-sm w-100 mt-2"
                            onClick={() => data.onRegenerateAudio(data.index)}
                            disabled={data.isRegeneratingAudio}>
                            <i className="bi bi-arrow-clockwise"></i> Regenerate Audio
                        </button>
                    </>
                )}
            </div>
            <Handle type="source" position={Position.Right} />
        </div>
    );
});

const nodeTypes = {
    paragraph: ParagraphNode
};

const NodeEditor: React.FC<NodeEditorProps> = ({ story: initialStory, onStyleUpdate }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState<Node<NodeData>[]>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<Edge[]>([]);
    const [selectedStyle, setSelectedStyle] = useState('realistic');
    const [expandedImage, setExpandedImage] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(!initialStory);
    const [story, setStory] = useState<Story | undefined>(initialStory);

    // Handle style updates
    const handleStyleChange = useCallback((index: number, style: string) => {
        setSelectedStyle(style);
        if (onStyleUpdate) {
            onStyleUpdate([{ index, image_style: style }]);
        }
    }, [onStyleUpdate]);

    const onConnect = useCallback((params: Connection) => {
        setEdges((eds) => addEdge({ ...params, type: 'smoothstep', animated: true }, eds));
    }, [setEdges]);

    const onNodeDragStop = useCallback<NodeDragHandler>((event, node) => {
        const currentPositions = localStorage.getItem('nodePositions');
        const savedPositions: SavedPositions = currentPositions ? JSON.parse(currentPositions) : {};
        
        // Update only the dragged node's position
        savedPositions[node.id] = node.position;
        localStorage.setItem('nodePositions', JSON.stringify(savedPositions));
        
        setNodes((nds) => nds.map((n) =>
            n.id === node.id ? { ...n, position: node.position } : n
        ));
    }, [setNodes]);

    const handleGenerateCard = useCallback(async (index: number) => {
        if (!initialStory?.paragraphs?.[index]) return;

        try {
            setNodes((nds) => nds.map((n) =>
                n.id === `p${index}` ? { ...n, data: { ...n.data, isGenerating: true } } : n
            ));

            const response = await fetch('/story/generate_cards', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index,
                    text: initialStory.paragraphs[index].text.trim(),
                    style: selectedStyle
                })
            });

            if (!response.ok) throw new Error('Failed to generate card');
            
            const data = await response.json();
            
            setNodes((nds) => nds.map((n) =>
                n.id === `p${index}` ? {
                    ...n,
                    data: {
                        ...n.data,
                        imageUrl: data.image_url,
                        imagePrompt: data.image_prompt,
                        audioUrl: data.audio_url,
                        isGenerating: false
                    }
                } : n
            ));
        } catch (error) {
            console.error('Error generating card:', error);
            setNodes((nds) => nds.map((n) =>
                n.id === `p${index}` ? { ...n, data: { ...n.data, isGenerating: false } } : n
            ));
        }
    }, [initialStory, selectedStyle]);

    const handleRegenerateImage = useCallback(async (index: number) => {
        if (!initialStory?.paragraphs?.[index]) return;

        try {
            setNodes((nds) => nds.map((n) =>
                n.id === `p${index}` ? { ...n, data: { ...n.data, isRegenerating: true } } : n
            ));

            const response = await fetch('/story/regenerate_image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index,
                    text: initialStory.paragraphs[index].text.trim(),
                    style: selectedStyle
                })
            });

            const data = await response.json();
            if (data.success) {
                setNodes((nds) => nds.map((n) =>
                    n.id === `p${index}` ? {
                        ...n,
                        data: {
                            ...n.data,
                            imageUrl: data.image_url,
                            imagePrompt: data.image_prompt,
                            isRegenerating: false
                        }
                    } : n
                ));
            }
        } catch (error) {
            console.error('Error regenerating image:', error);
            setNodes((nds) => nds.map((n) =>
                n.id === `p${index}` ? { ...n, data: { ...n.data, isRegenerating: false } } : n
            ));
        }
    }, [initialStory, selectedStyle]);

    const handleRegenerateAudio = useCallback(async (index: number) => {
        if (!initialStory?.paragraphs?.[index]) return;

        try {
            setNodes((nds) => nds.map((n) =>
                n.id === `p${index}` ? { ...n, data: { ...n.data, isRegeneratingAudio: true } } : n
            ));

            const response = await fetch('/story/regenerate_audio', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index,
                    text: initialStory.paragraphs[index].text.trim()
                })
            });

            const data = await response.json();
            if (data.success) {
                setNodes((nds) => nds.map((n) =>
                    n.id === `p${index}` ? {
                        ...n,
                        data: {
                            ...n.data,
                            audioUrl: data.audio_url,
                            isRegeneratingAudio: false
                        }
                    } : n
                ));
            }
        } catch (error) {
            console.error('Error regenerating audio:', error);
            setNodes((nds) => nds.map((n) =>
                n.id === `p${index}` ? { ...n, data: { ...n.data, isRegeneratingAudio: false } } : n
            ));
        }
    }, [initialStory]);

    // Node drag handler is already defined above

    // Load saved positions and initialize nodes
    useEffect(() => {
        if (!initialStory?.paragraphs) return;

        const savedPositions = localStorage.getItem('nodePositions');
        const positions: SavedPositions = savedPositions ? JSON.parse(savedPositions) : {};

        const newNodes = initialStory.paragraphs.map((para, index) => ({
            id: `p${index}`,
            type: 'paragraph',
            position: positions[`p${index}`] || {
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
                onRegenerateImage: handleRegenerateImage,
                onRegenerateAudio: handleRegenerateAudio,
                onExpandImage: setExpandedImage,
                onStyleChange: handleStyleChange,
                isGenerating: false,
                isRegenerating: false,
                isRegeneratingAudio: false
            }
        }));

        setNodes(newNodes);
        setIsLoading(false);
    }, [initialStory, selectedStyle, handleGenerateCard, handleRegenerateImage, handleRegenerateAudio, handleStyleChange, setNodes]);

    const renderContent = () => {
        if (isLoading || !story?.paragraphs) {
            return (
                <div className="flex items-center justify-center h-96">
                    <div className="text-lg">Loading story data...</div>
                </div>
            );
        }

        return (
            <div style={{ width: '100%', height: '600px' }} className="node-editor-root">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    onNodeDragStop={onNodeDragStop}
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

    return (
        <>
            {renderContent()}
            {expandedImage && (
                <div className="modal-backdrop" onClick={() => setExpandedImage(null)}>
                    <div className="preview-modal" onClick={e => e.stopPropagation()}>
                        <button 
                            type="button" 
                            className="close-button"
                            onClick={() => setExpandedImage(null)}
                        >
                            ×
                        </button>
                        <div className="preview-content">
                            <img src={expandedImage} alt="Full preview" />
                        </div>
                    </div>
                </div>
            )}
        </>
    );

    if (!story?.paragraphs?.length) {
        return (
            <div className="flex items-center justify-center h-96">
                No story data available
            </div>
        );
    }

    return (
        <>
            <div style={{ width: '100%', height: '600px' }} className="node-editor-root">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    onNodeDragStop={onNodeDragStop}
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
            
            {expandedImage && (
                <div className="modal-backdrop" onClick={() => setExpandedImage(null)}>
                    <div className="preview-modal" onClick={e => e.stopPropagation()}>
                        <button 
                            type="button" 
                            className="close-button"
                            onClick={() => setExpandedImage(null)}
                        >
                            ×
                        </button>
                        <div className="preview-content">
                            <img src={expandedImage} alt="Full preview" />
                        </div>
                    </div>
                </div>
            )}
        </>
    );
        }, {});
        
        localStorage.setItem('nodePositions', JSON.stringify(nodePositions));
        
        setNodes((nds) => nds.map((n) =>
            n.id === node.id ? { ...n, position: node.position } : n
        ));
    }, [nodes, setNodes]);

    return (
        <>
            {isLoading ? (
                <div className="flex items-center justify-center h-96">
                    Loading story data...
                </div>
            ) : !initialStory?.paragraphs?.length ? (
                <div className="flex items-center justify-center h-96">
                    No story data available.
                </div>
            ) : (
                <div className="relative w-full h-[600px]">
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onConnect={onConnect}
                        onNodeDragStop={onNodeDragStop}
                        nodeTypes={nodeTypes}
                        fitView
                        className="bg-background"
                        minZoom={0.1}
                        maxZoom={4}
                        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
                    >
                        <Background />
                        <Controls />
                    </ReactFlow>
                </div>
            )}
            
            {expandedImage && (
                <div 
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
                    onClick={() => setExpandedImage(null)}
                >
                    <div 
                        className="relative max-w-4xl max-h-[90vh] bg-background rounded-lg p-4"
                        onClick={e => e.stopPropagation()}
                    >
                        <button 
                            className="absolute top-2 right-2 text-muted-foreground hover:text-foreground"
                            onClick={() => setExpandedImage(null)}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                        <img 
                            src={expandedImage} 
                            alt="Expanded preview" 
                            className="max-w-full max-h-[85vh] object-contain rounded-lg"
                        />
                    </div>
                </div>
            )}
        </>
    );
    const [selectedStyle, setSelectedStyle] = useState('realistic');
    const [expandedImage, setExpandedImage] = useState<string | null>(null);
    const [story, setStory] = useState<Story | undefined>(initialStory);
    const [isLoading, setIsLoading] = useState(!initialStory);

    // Load saved node positions from localStorage
    useEffect(() => {
        const savedPositions = localStorage.getItem('nodePositions');
        if (savedPositions && story?.paragraphs) {
            const positions = JSON.parse(savedPositions);
            const nodesWithSavedPositions = story.paragraphs.map((para, index) => ({
                id: `p${index}`,
                type: 'paragraph',
                position: positions[`p${index}`] || { 
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
                    onRegenerateImage: handleRegenerateImage,
                    onRegenerateAudio: handleRegenerateAudio,
                    onExpandImage: setExpandedImage,
                    onStyleChange: handleStyleChange,
                    isGenerating: false,
                    isRegenerating: false,
                    isRegeneratingAudio: false
                }
            }));
            setNodes(nodesWithSavedPositions);
        }
    }, [story, selectedStyle]);

    const handleRegenerateImage = useCallback(async (index: number) => {
        try {
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegenerating: true}} : node
            ));

            const response = await fetch('/story/regenerate_image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index,
                    text: story?.paragraphs[index].text,
                    style: nodes.find(n => n.id === `p${index}`)?.data.globalStyle || 'realistic',
                    regenerate_prompt: true
                })
            });

            const data = await response.json();
            if (data.success) {
                setNodes(nodes => nodes.map(node => 
                    node.id === `p${index}` ? {
                        ...node, 
                        data: {
                            ...node.data,
                            imageUrl: data.image_url,
                            imagePrompt: data.image_prompt,
                            isRegenerating: false
                        }
                    } : node
                ));
            }
        } catch (error) {
            console.error('Error regenerating image:', error);
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegenerating: false}} : node
            ));
        }
    }, [story, nodes]);

    const handleStyleChange = useCallback((index: number, newStyle: string) => {
        // Update local style
        setNodes(nodes => nodes.map(node => 
            node.id === `p${index}` ? {
                ...node,
                data: {
                    ...node.data,
                    globalStyle: newStyle
                }
            } : node
        ));
        
        // Get the current paragraph text
        const paragraphText = story?.paragraphs[index]?.text;
        
        // Update backend and regenerate image with new style
        fetch('/story/update_style', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                paragraphs: [{
                    index,
                    image_style: newStyle,
                    text: paragraphText
                }]
            })
        }).then(() => {
            // After style is updated, regenerate the image with new prompt
            handleRegenerateImage(index);
        });
    }, [story, handleRegenerateImage]);

    const handleGenerateCard = useCallback(async (index: number) => {
        try {
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: true}} : node
            ));

            const response = await fetch('/story/generate_cards', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index,
                    text: story?.paragraphs[index].text,
                    style: nodes.find(n => n.id === `p${index}`)?.data.globalStyle || 'realistic'
                })
            });

            const reader = response.body?.getReader();
            if (!reader) throw new Error('Failed to get reader');

            // Handle streaming response
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
                    
                    const data = JSON.parse(line);
                    if (data.type === 'paragraph') {
                        setNodes(nodes => nodes.map(node => 
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
                        ));
                    }
                }
            }
        } catch (error) {
            console.error('Error generating card:', error);
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: false}} : node
            ));
        }
    }, [story, selectedStyle]);

    // Removed duplicate declaration

    const handleRegenerateAudio = useCallback(async (index: number) => {
        try {
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegeneratingAudio: true}} : node
            ));

            const response = await fetch('/story/regenerate_audio', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index,
                    text: story?.paragraphs[index].text
                })
            });

            const data = await response.json();
            if (data.success) {
                setNodes(nodes => nodes.map(node => 
                    node.id === `p${index}` ? {
                        ...node, 
                        data: {
                            ...node.data,
                            audioUrl: data.audio_url,
                            isRegeneratingAudio: false
                        }
                    } : node
                ));
            }
        } catch (error) {
            console.error('Error regenerating audio:', error);
            setNodes(nodes => nodes.map(node => 
    const onNodeDragStop = useCallback((event: React.MouseEvent, node: Node<NodeData>) => {
        setNodes((nds) => {
            const updatedNodes = nds.map((n) => 
                n.id === node.id ? { ...n, position: node.position } : n
            );
            // Save positions to localStorage
            const positions = updatedNodes.reduce((acc, n) => ({
                ...acc,
                [n.id]: n.position
            }), {});
            localStorage.setItem('nodePositions', JSON.stringify(positions));
            return updatedNodes;
        });
    }, [setNodes]);

    // Load saved positions on mount
    useEffect(() => {
        const savedPositions = localStorage.getItem('nodePositions');
        if (savedPositions && story?.paragraphs) {
            const positions = JSON.parse(savedPositions);
            const nodesWithSavedPositions = story.paragraphs.map((para, index) => ({
                id: `p${index}`,
                type: 'paragraph',
                position: positions[`p${index}`] || { 
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
                    onRegenerateImage: handleRegenerateImage,
                    onRegenerateAudio: handleRegenerateAudio,
                    onExpandImage: setExpandedImage,
                    onStyleChange: handleStyleChange,
                    isGenerating: false,
                    isRegenerating: false,
                    isRegeneratingAudio: false
                }
            }));
            setNodes(nodesWithSavedPositions);
        }
    }, [story, selectedStyle, handleGenerateCard, handleRegenerateImage, handleRegenerateAudio, handleStyleChange]);
    }, [setNodes]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary"></div>
                <span className="ml-2">Loading story data...</span>
            </div>
        );
    }

    if (!story?.paragraphs?.length) {
        return (
            <div className="flex items-center justify-center h-96 text-gray-600">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>No story data available</span>
            </div>
        );
    }

    return (
        <div className="relative">
            <div style={{ width: '100%', height: '600px' }} className="node-editor-root bg-background">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    nodeTypes={nodeTypes}
                    onNodeDragStop={onNodeDragStop}
                    fitView
                    style={{ background: 'var(--background)' }}
                    minZoom={0.1}
                    maxZoom={4}
                    defaultViewport={{ x: 0, y: 0, zoom: 1 }}
                    connectOnClick={true}
                >
                    <Background />
                    <Controls />
                </ReactFlow>
            </div>
            
            {expandedImage && (
                <div 
                    className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
                    onClick={() => setExpandedImage(null)}
                >
                    <div 
                        className="relative bg-background rounded-lg p-4 max-w-4xl max-h-[90vh] w-full m-4"
                        onClick={e => e.stopPropagation()}
                    >
                        <button 
                            type="button" 
                            className="absolute top-2 right-2 text-gray-500 hover:text-gray-700"
                            onClick={() => setExpandedImage(null)}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                        <div className="mt-4 overflow-auto">
                            <img 
                                src={expandedImage} 
                                alt="Full preview" 
                                className="max-w-full h-auto"
                                onError={(e) => {
                                    console.error('Failed to load expanded image:', expandedImage);
                                    e.currentTarget.src = '/static/placeholder.png';
                                }}
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
                node.id === `p${index}` ? {...node, data: {...node.data, isRegeneratingAudio: false}} : node
            ));
        }
    }, [story, selectedStyle]);

    useEffect(() => {
        const fetchStoryData = async () => {
            try {
                const response = await fetch('/api/story/data');
                const data = await response.json();
                if (data.success) {
                    setStory(data.story);
                }
            } catch (error) {
                console.error('Error fetching story data:', error);
                setIsLoading(false);
            }
        };

        if (!story) {
            fetchStoryData();
        }
    }, [story]);

    // Store node positions in localStorage
    const saveNodePositions = useCallback((nodes: Node[]) => {
        const positions = nodes.reduce((acc, node) => ({
            ...acc,
            [node.id]: node.position
        }), {});
        localStorage.setItem('nodePositions', JSON.stringify(positions));
    }, []);

    // Load saved positions from localStorage
    const loadSavedPositions = useCallback(() => {
        try {
            const saved = localStorage.getItem('nodePositions');
            return saved ? JSON.parse(saved) : null;
        } catch (error) {
            console.error('Error loading saved positions:', error);
            return null;
        }
    }, []);

    useEffect(() => {
        if (!story?.paragraphs) {
            setIsLoading(false);
            return;
        }

        const savedPositions = loadSavedPositions();
        
        const paragraphNodes = story.paragraphs.map((para, index) => {
            const nodeId = `p${index}`;
            const defaultPosition = { 
                x: (index % 3) * 500 + 50,
                y: Math.floor(index / 3) * 450 + 50
            };

            return {
                id: nodeId,
                type: 'paragraph',
                draggable: true,
                position: savedPositions?.[nodeId] || defaultPosition,
                data: {
                    index,
                    text: para.text,
                    globalStyle: selectedStyle,
                    imageUrl: para.image_url,
                imagePrompt: para.image_prompt,
                audioUrl: para.audio_url,
                onGenerateCard: handleGenerateCard,
                onRegenerateImage: handleRegenerateImage,
                onRegenerateAudio: handleRegenerateAudio,
                onExpandImage: setExpandedImage,
                isGenerating: false,
                isRegenerating: false,
                isRegeneratingAudio: false
            }
        }));

        setNodes(paragraphNodes);
        setIsLoading(false);
    }, [story, selectedStyle, handleGenerateCard, handleRegenerateImage, handleRegenerateAudio]);

    // Rest of the component implementation remains the same, just with proper TypeScript types
    // ...

    if (isLoading) {
        return <div className="flex items-center justify-center h-96">Loading story data...</div>;
    }

    if (!story?.paragraphs?.length) {
        return <div className="flex items-center justify-center h-96">No story data available</div>;
    }

    const renderContent = () => {
        if (isLoading) {
            return <div className="flex items-center justify-center h-96">Loading story data...</div>;
        }

        if (!story?.paragraphs?.length) {
            return <div className="flex items-center justify-center h-96">No story data available</div>;
        }

        return (
            <>
            <div style={{ width: '100%', height: '600px' }} className="node-editor-root">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
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
            
            {expandedImage && (
                <div 
                    className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center backdrop-blur-sm"
                    onClick={() => setExpandedImage(null)}
                >
                    <div 
                        className="relative bg-background rounded-lg p-4 max-w-4xl max-h-[90vh] w-full mx-4"
                        onClick={e => e.stopPropagation()}
                    >
                        <Button
                            variant="ghost"
                            size="icon"
                            className="absolute right-2 top-2"
                            onClick={() => setExpandedImage(null)}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M18 6L6 18M6 6l12 12"/>
                            </svg>
                        </Button>
                        <div className="overflow-auto">
                            <img 
                                src={expandedImage} 
                                alt="Full preview" 
                                className="w-full h-auto rounded-lg"
                            />
                        </div>
                    </div>
                </div>
            )}
        </>
        );
    };

    return renderContent();
};

export default React.memo(NodeEditor);
