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
    Edge
} from 'reactflow';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
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
    const [story, setStory] = useState<Story | undefined>(initialStory);
    const [isLoading, setIsLoading] = useState(!initialStory);
    const [hasError, setHasError] = useState(false);
    const initializationRef = useRef(false);

    // Validate story data and update state
    useEffect(() => {
        if (!initialStory?.paragraphs || initializationRef.current) {
            if (!initialStory?.paragraphs) {
                console.error('Invalid story data:', initialStory);
                setHasError(true);
            }
            setIsLoading(false);
            return;
        }

        console.log('Initializing with story:', initialStory);
        
        try {
            // Validate story structure
            const isValidStory = initialStory.paragraphs.every(para => 
                typeof para.text === 'string' && para.text.trim().length > 0
            );

            if (!isValidStory) {
                throw new Error('Invalid story structure: missing or invalid paragraph text');
            }

            setStory(initialStory);
            setHasError(false);
            initializationRef.current = true;
        } catch (error) {
            console.error('Story validation error:', error);
            setHasError(true);
        } finally {
            setIsLoading(false);
        }

        // Cleanup function
        return () => {
            setNodes([]);
            setEdges([]);
            initializationRef.current = false;
        };
    }, [initialStory, setNodes, setEdges]);

    // Initialize nodes when story data changes
    useEffect(() => {
        if (!story?.paragraphs || !initializationRef.current) {
            return;
        }

        try {
            console.log('Initializing nodes with paragraphs:', story.paragraphs.length);
            const paragraphNodes = story.paragraphs.map((para, index) => ({
                id: `p${index}`,
                type: 'paragraph',
                position: { 
                    x: (index % 3) * 400 + 50,
                    y: Math.floor(index / 3) * 300 + 50
                },
                draggable: true,
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

            setNodes(paragraphNodes);
            setIsInitialized(true);
        } catch (error) {
            console.error('Error initializing nodes:', error);
            setHasError(true);
        }
    }, [story, selectedStyle, isInitialized]);

    const handleRegenerateImage = useCallback(async (index: number) => {
        if (!story?.paragraphs?.[index]) {
            console.error('Invalid paragraph index:', index);
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
        if (!story?.paragraphs?.[index]) {
            console.error('Invalid paragraph index:', index);
            return;
        }

        setNodes(nodes => nodes.map(node => 
            node.id === `p${index}` ? {
                ...node,
                data: {
                    ...node.data,
                    globalStyle: newStyle
                }
            } : node
        ));
        
        fetch('/story/update_style', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                paragraphs: [{
                    index,
                    image_style: newStyle,
                    text: story.paragraphs[index].text
                }]
            })
        }).then(() => {
            handleRegenerateImage(index);
        }).catch(error => {
            console.error('Error updating style:', error);
        });
    }, [story, handleRegenerateImage]);

    const handleGenerateCard = useCallback(async (index: number) => {
        if (!story?.paragraphs?.[index]) {
            console.error('Invalid paragraph index:', index);
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
                    style: nodes.find(n => n.id === `p${index}`)?.data.globalStyle || 'realistic'
                })
            });

            if (!response.ok) throw new Error('Failed to generate card');

            const reader = response.body?.getReader();
            if (!reader) throw new Error('Failed to get reader');

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
                                        audioUrl: data.data.audio_url,
                                        isGenerating: false
                                    }
                                } : node
                            ));
                        }
                    } catch (error) {
                        console.error('Error parsing JSON:', error);
                    }
                }
            }
        } catch (error) {
            console.error('Error generating card:', error);
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: false}} : node
            ));
        }
    }, [story, nodes]);

    const handleRegenerateAudio = useCallback(async (index: number) => {
        if (!story?.paragraphs?.[index]) {
            console.error('Invalid paragraph index:', index);
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
    }, [story]);

    const onConnect = useCallback((params: any) => {
        if (params.source === params.target) return;
        
        const edge = {
            ...params,
            type: 'smoothstep',
            animated: true,
            style: { 
                stroke: 'var(--bs-primary)',
                strokeWidth: 2,
            }
        };
        
        setEdges(edges => addEdge(edge, edges));
    }, [setEdges]);

    if (hasError) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center p-4">
                    <h3 className="text-lg font-semibold text-red-500">Error Loading Story</h3>
                    <p className="text-sm text-gray-600">Please try refreshing the page</p>
                </div>
            </div>
        );
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center p-4">
                    <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                    <p className="text-sm text-gray-600">Loading story...</p>
                </div>
            </div>
        );
    }

    // Render loading state or error message
    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-[600px] bg-background">
                <div className="text-center">
                    <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p>Loading story data...</p>
                </div>
            </div>
        );
    }

    if (hasError) {
        return (
            <div className="flex items-center justify-center h-[600px] bg-background">
                <div className="text-center text-destructive">
                    <h3 className="text-lg font-semibold mb-2">Error Loading Story</h3>
                    <p>Unable to initialize story editor. Please try refreshing the page.</p>
                </div>
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
};

export default React.memo(NodeEditor);
