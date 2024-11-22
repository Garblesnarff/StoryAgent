import React, { useState, useCallback, useEffect } from 'react';
import ReactFlow, { 
    Controls, 
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    Handle,
    Position,
    Node,
    Edge
} from 'reactflow';
import { Button } from '@/components/ui/button';
import 'reactflow/dist/style.css';

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

const ParagraphNode = React.memo(({ data }: { data: ParagraphData }) => {
    const [showPrompt, setShowPrompt] = useState(false);
    const [localStyle, setLocalStyle] = useState(data.globalStyle || 'realistic');

    return (
        <div className="bg-card rounded-lg shadow-lg p-4 min-w-[400px] max-w-[400px] border border-border">
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
                                className="w-full h-auto"
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
                        <div className="audio-player mt-2">
                            <audio controls className="w-100" key={data.audioUrl}>
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

const NodeEditor: React.FC<NodeEditorProps> = ({ story: initialStory, onStyleUpdate }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [selectedStyle, setSelectedStyle] = useState('realistic');
    const [expandedImage, setExpandedImage] = useState<string | null>(null);
    const [story, setStory] = useState(initialStory);
    const [isLoading, setIsLoading] = useState(!initialStory);

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
                    style: selectedStyle
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
            console.error('Error regenerating image:', error);
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegenerating: false}} : node
            ));
        }
    }, [story, selectedStyle]);

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

    useEffect(() => {
        if (!story?.paragraphs) {
            setIsLoading(false);
            return;
        }

        const paragraphNodes = story.paragraphs.map((para, index) => ({
            id: `p${index}`,
            type: 'paragraph',
            position: { 
                x: (index % 3) * 450 + 50, // Arrange in 3 columns
                y: Math.floor(index / 3) * 400 + 50 // More vertical spacing
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

export default React.memo(NodeEditor);
