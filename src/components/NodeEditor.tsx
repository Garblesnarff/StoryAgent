import React, { useState, useCallback, useLayoutEffect } from 'react';
import ReactFlow, { 
    Controls, 
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    Handle,
    Position,
    Node,
    Edge,
    Connection,
    ReactFlowProvider
} from 'reactflow';
import { Button } from '@/components/ui/button';
import 'reactflow/dist/style.css';

// Loading Component
const LoadingState = () => (
    <div className="flex items-center justify-center h-[600px] bg-background border rounded-lg">
        <div className="space-y-4 text-center">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-muted-foreground">Loading story editor...</p>
        </div>
    </div>
);

interface NodeData {
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

interface Story {
    paragraphs: Array<{
        text: string;
        image_url?: string;
        image_prompt?: string;
        audio_url?: string;
    }>;
}

interface NodeEditorProps {
    story?: Story;
    onStyleUpdate?: (paragraphs: Array<{ index: number; image_style: string }>) => void;
}

const ParagraphNode = React.memo(({ data }: { data: NodeData }) => {
    const [showPrompt, setShowPrompt] = useState(false);

    return (
        <div className={`paragraph-node ${data.globalStyle}-style`}>
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
                
                {data.imageUrl && (
                    <>
                        <div className="relative rounded-lg overflow-hidden border border-border">
                            <img 
                                src={data.imageUrl} 
                                alt="Generated preview" 
                                className="w-full h-auto object-cover"
                                onError={(e) => {
                                    console.error('[ParagraphNode] Image failed to load:', data.imageUrl);
                                    e.currentTarget.src = '/static/placeholder.png';
                                }}
                            />
                            {showPrompt && data.imagePrompt && (
                                <div className="absolute inset-0 bg-black/75 p-4 text-white overflow-y-auto">
                                    <p className="text-sm">{data.imagePrompt}</p>
                                </div>
                            )}
                            <div className="flex gap-2 p-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="flex-1"
                                    onClick={() => data.onRegenerateImage(data.index)}
                                    disabled={data.isRegenerating}>
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
                                    onClick={() => setShowPrompt(!showPrompt)}>
                                    {showPrompt ? 'Hide Prompt' : 'Show Prompt'}
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => data.onExpandImage(data.imageUrl!)}>
                                    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
                                    </svg>
                                </Button>
                            </div>
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
                                onError={(e) => console.error('[ParagraphNode] Audio failed to load:', data.audioUrl)}>
                                <source src={data.audioUrl} type="audio/wav" />
                                Your browser does not support the audio element.
                            </audio>
                        </div>
                        <Button 
                            variant="outline"
                            size="sm"
                            className="w-full mt-2"
                            onClick={() => data.onRegenerateAudio(data.index)}
                            disabled={data.isRegeneratingAudio}>
                            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                                <path d="M3 3v5h5" />
                                <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
                                <path d="M16 16h5v5" />
                            </svg>
                            Regenerate Audio
                        </Button>
                    </>
                )}
            </div>
            <Handle type="source" position={Position.Right} className="!bg-primary" />
        </div>
    );
});

const nodeTypes = {
    paragraph: ParagraphNode
};

const NodeEditor: React.FC<NodeEditorProps> = ({ story: initialStory, onStyleUpdate }) => {
    console.log('[NodeEditor] Props received:', { initialStory });
    
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [selectedStyle, setSelectedStyle] = useState('realistic');
    const [expandedImage, setExpandedImage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

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
                    text: initialStory?.paragraphs[index].text,
                    style: selectedStyle
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
            console.error('[NodeEditor] Error regenerating image:', error);
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegenerating: false}} : node
            ));
        }
    }, [initialStory, selectedStyle]);

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
                    text: initialStory?.paragraphs[index].text
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
            console.error('[NodeEditor] Error regenerating audio:', error);
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegeneratingAudio: false}} : node
            ));
        }
    }, [initialStory]);

    const handleGenerateCard = useCallback(async (index: number) => {
        if (!initialStory?.paragraphs?.[index]?.text) {
            console.error('[NodeEditor] No text found for paragraph');
            return;
        }

        try {
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: true}} : node
            ));

            const response = await fetch('/story/generate_cards', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index,
                    text: initialStory.paragraphs[index].text,
                    style: selectedStyle
                })
            });

            if (!response.ok) throw new Error('Failed to generate card');
            
            const data = await response.json();
            if (data.success) {
                setNodes(nodes => nodes.map(node => 
                    node.id === `p${index}` ? {
                        ...node, 
                        data: {
                            ...node.data,
                            imageUrl: data.image_url,
                            imagePrompt: data.image_prompt,
                            audioUrl: data.audio_url,
                            isGenerating: false
                        }
                    } : node
                ));
            }
        } catch (error) {
            console.error('[NodeEditor] Error generating card:', error);
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: false}} : node
            ));
        }
    }, [initialStory, selectedStyle]);

    const handleStyleChange = useCallback((index: number, newStyle: string) => {
        setNodes(nodes => nodes.map(node => 
            node.id === `p${index}` ? {
                ...node,
                data: {
                    ...node.data,
                    globalStyle: newStyle
                }
            } : node
        ));

        if (onStyleUpdate) {
            onStyleUpdate([{ index, image_style: newStyle }]);
        }
    }, [onStyleUpdate]);

    useLayoutEffect(() => {
        console.log('[NodeEditor] Initializing with story:', initialStory);
        
        if (!initialStory?.paragraphs) {
            setError('Story data is missing');
            setIsLoading(false);
            return;
        }

        try {
            const newNodes = initialStory.paragraphs.map((para, index) => ({
                id: `p${index}`,
                type: 'paragraph',
                position: { x: (index % 3) * 500 + 50, y: Math.floor(index / 3) * 450 + 50 },
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
            
            console.log('[NodeEditor] Setting up nodes:', newNodes);
            setNodes(newNodes);
            setIsLoading(false);
        } catch (err) {
            console.error('[NodeEditor] Error setting up nodes:', err);
            setError('Failed to initialize story editor');
            setIsLoading(false);
        }
    }, [initialStory, selectedStyle, handleGenerateCard, handleRegenerateImage, handleRegenerateAudio, handleStyleChange]);

    const onConnect = useCallback((params: Connection) => {
        const edge = {
            ...params,
            type: 'smoothstep',
            animated: true,
            style: { 
                stroke: 'var(--primary)',
                strokeWidth: 2,
            }
        };
        
        setEdges(edges => addEdge(edge, edges));
    }, [setEdges]);

    if (error) {
        return (
            <div className="flex items-center justify-center h-[600px] bg-background border rounded-lg">
                <div className="text-center space-y-4">
                    <p className="text-red-500">{error}</p>
                    <Button onClick={() => window.location.reload()}>
                        Retry
                    </Button>
                </div>
            </div>
        );
    }

    if (isLoading) {
        return <LoadingState />;
    }

    return (
        <>
            <div style={{ width: '100%', height: '600px' }} className="bg-background border rounded-lg">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    nodeTypes={nodeTypes}
                    fitView
                    minZoom={0.1}
                    maxZoom={4}
                    defaultViewport={{ x: 0, y: 0, zoom: 1 }}>
                    <Background />
                    <Controls />
                </ReactFlow>
            </div>
            
            {expandedImage && (
                <div 
                    className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
                    onClick={() => setExpandedImage(null)}>
                    <div 
                        className="bg-background p-4 rounded-lg max-w-4xl max-h-[90vh] overflow-auto"
                        onClick={e => e.stopPropagation()}>
                        <Button 
                            variant="ghost"
                            size="sm"
                            className="absolute top-2 right-2"
                            onClick={() => setExpandedImage(null)}>
                            ×
                        </Button>
                        <img 
                            src={expandedImage} 
                            alt="Full preview" 
                            className="max-w-full h-auto"
                        />
                    </div>
                </div>
            )}
        </>
    );
};

export default React.memo(NodeEditor);