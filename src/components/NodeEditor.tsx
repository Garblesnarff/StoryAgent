import React, { useState, useCallback, useEffect, useRef } from 'react';
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
    Viewport
} from 'reactflow';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import 'reactflow/dist/style.css';

// TypeScript Types
type ImageStyle = 'realistic' | 'artistic' | 'fantasy';

interface Paragraph {
    text: string;
    image_url?: string;
    image_prompt?: string;
    audio_url?: string;
    image_style?: ImageStyle;
}

interface Story {
    paragraphs: Paragraph[];
}

interface ParagraphData {
    index: number;
    text: string;
    globalStyle: ImageStyle;
    imageUrl?: string;
    imagePrompt?: string;
    audioUrl?: string;
    onGenerateCard: (index: number) => Promise<void>;
    onRegenerateImage: (index: number) => Promise<void>;
    onRegenerateAudio: (index: number) => Promise<void>;
    onExpandImage: (url: string) => void;
    onStyleChange?: (index: number, style: ImageStyle) => void;
    isGenerating: boolean;
    isRegenerating: boolean;
    isRegeneratingAudio: boolean;
}

interface NodeEditorProps {
    story?: Story;
    onStyleUpdate?: (paragraphs: Array<{ index: number; image_style: ImageStyle }>) => void;
}

// Type Guards
const isValidParagraph = (paragraph: unknown): paragraph is Paragraph => {
    if (!paragraph || typeof paragraph !== 'object') return false;
    const p = paragraph as Paragraph;
    return typeof p.text === 'string' && p.text.length > 0;
};

const isValidStory = (story: unknown): story is Story => {
    if (!story || typeof story !== 'object') return false;
    const s = story as Story;
    return Array.isArray(s.paragraphs) && s.paragraphs.every(isValidParagraph);
};

// Component Definition
const NodeEditor: React.FC<NodeEditorProps> = ({ story: initialStory, onStyleUpdate }) => {
    // State Management
    const [nodes, setNodes, onNodesChange] = useNodesState<Node<ParagraphData>[]>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<Edge[]>([]);
    const [selectedStyle, setSelectedStyle] = useState<ImageStyle>('realistic');
    const [expandedImage, setExpandedImage] = useState<string | null>(null);
    const [story, setStory] = useState<Story | undefined>(undefined);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Handler Functions
    const handleRegenerateImage = useCallback(async (index: number) => {
        if (!story?.paragraphs[index]) {
            console.error('Invalid paragraph index for image regeneration');
            return;
        }

        try {
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegenerating: true}} : node
            ));

            const response = await fetch('/story/regenerate_image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index,
                    text: story.paragraphs[index].text,
                    style: selectedStyle,
                    regenerate_prompt: true
                })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Failed to regenerate image');

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
            setError(error instanceof Error ? error.message : 'Failed to regenerate image');
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegenerating: false}} : node
            ));
        }
    }, [story, selectedStyle]);

    const handleRegenerateAudio = useCallback(async (index: number) => {
        if (!story?.paragraphs[index]) {
            console.error('Invalid paragraph index for audio regeneration');
            return;
        }

        try {
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegeneratingAudio: true}} : node
            ));

            const response = await fetch('/story/regenerate_audio', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index,
                    text: story.paragraphs[index].text
                })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Failed to regenerate audio');

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
            setError(error instanceof Error ? error.message : 'Failed to regenerate audio');
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegeneratingAudio: false}} : node
            ));
        }
    }, [story]);

    const handleGenerateCard = useCallback(async (index: number) => {
        if (!story?.paragraphs[index]) {
            console.error('Invalid paragraph index for card generation');
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
                    text: story.paragraphs[index].text,
                    style: selectedStyle
                })
            });

            if (!response.ok) throw new Error('Failed to generate card');
            
            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            
            if (!reader) throw new Error('Failed to read response');

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
                            setNodes(nodes => 
                                nodes.map(node => 
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
                                )
                            );
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
            setError(error instanceof Error ? error.message : 'Failed to generate card');
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: false}} : node
            ));
        }
    }, [story, selectedStyle]);

    const handleStyleChange = useCallback((index: number, newStyle: ImageStyle) => {
        setNodes(prevNodes => {
            if (prevNodes.length === 0) {
                console.warn('No nodes present during style update');
                return prevNodes;
            }
            
            return prevNodes.map(node => 
                node.id === `p${index}` ? {
                    ...node,
                    data: {
                        ...node.data,
                        globalStyle: newStyle
                    }
                } : node
            );
        });

        onStyleUpdate?.([{
            index,
            image_style: newStyle
        }]);
    }, [onStyleUpdate]);

    // Story Initialization Effect
    useEffect(() => {
        console.log('Story data update:', {
            initialStory,
            isValid: isValidStory(initialStory),
            paragraphCount: initialStory?.paragraphs?.length
        });

        if (!isValidStory(initialStory)) {
            console.error('Invalid story data:', initialStory);
            setError('Invalid story data provided');
            setIsLoading(false);
            return;
        }

        setStory(initialStory);
    }, [initialStory]);

    // Node Initialization Effect
    useEffect(() => {
        if (!story) {
            console.log('No story available for node initialization');
            return;
        }

        console.log('Initializing nodes for story:', {
            paragraphCount: story.paragraphs.length,
            selectedStyle
        });

        try {
            setIsLoading(true);

            // Calculate viewport dimensions
            const VIEWPORT_WIDTH = 1200;
            const VIEWPORT_HEIGHT = 800;
            const NODE_WIDTH = 400;
            const NODE_HEIGHT = 300;
            const HORIZONTAL_SPACING = NODE_WIDTH + 200;
            const VERTICAL_SPACING = NODE_HEIGHT + 150;

            const paragraphNodes = story.paragraphs.map((para, index) => {
                // Calculate grid-based position with proper spacing
                const row = Math.floor(index / 2);
                const col = index % 2;
                const xPos = (col * HORIZONTAL_SPACING) + (VIEWPORT_WIDTH - HORIZONTAL_SPACING) / 4;
                const yPos = (row * VERTICAL_SPACING) + 100;

                return {
                    id: `p${index}`,
                    type: 'paragraph',
                    position: { x: xPos, y: yPos },
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
                };
            });

            setNodes(paragraphNodes);
            console.log('Successfully initialized nodes:', {
                nodeCount: paragraphNodes.length
            });
        } catch (error) {
            console.error('Error initializing nodes:', error);
            setError('Failed to initialize story nodes');
        } finally {
            setIsLoading(false);
        }
    }, [story, selectedStyle, handleGenerateCard, handleRegenerateImage, handleRegenerateAudio, handleStyleChange]);

    // Error and Loading States
    if (isLoading) {
        return <div className="flex items-center justify-center h-[600px] bg-background">
            <div className="flex flex-col items-center gap-4">
                <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                <p className="text-muted-foreground">Initializing story editor...</p>
            </div>
        </div>;
    }

    if (error) {
        return <div className="flex items-center justify-center h-[600px] bg-background">
            <div className="flex flex-col items-center gap-4 max-w-md text-center">
                <div className="text-destructive">
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="8" x2="12" y2="12" />
                        <line x1="12" y1="16" x2="12" y2="16" />
                    </svg>
                </div>
                <p className="text-destructive">{error}</p>
                <Button variant="outline" onClick={() => window.location.reload()}>
                    Retry
                </Button>
            </div>
        </div>;
    }

    // Render Flow Editor
    return (
        <>
            <div style={{ width: '100%', height: '600px' }} className="node-editor-root">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={(params) => {
                        if (params.source === params.target) return;
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
                    }}
                    nodeTypes={{ paragraph: ParagraphNode }}
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
                    className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50"
                    onClick={() => setExpandedImage(null)}
                >
                    <div 
                        className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-card p-4 rounded-lg shadow-lg"
                        onClick={e => e.stopPropagation()}
                    >
                        <Button 
                            variant="ghost"
                            size="icon"
                            className="absolute top-2 right-2"
                            onClick={() => setExpandedImage(null)}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <line x1="18" y1="6" x2="6" y2="18" />
                                <line x1="6" y1="6" x2="18" y2="18" />
                            </svg>
                        </Button>
                        <img 
                            src={expandedImage} 
                            alt="Full preview" 
                            className="max-w-[90vw] max-h-[90vh] object-contain"
                        />
                    </div>
                </div>
            )}
        </>
    );
};

const ParagraphNode: React.FC<{ data: ParagraphData }> = ({ data }) => {
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

export default React.memo(NodeEditor);