import React from 'react';
import { createRoot } from 'react-dom/client';
import NodeEditor from './node-editor';
import { DndContext, DragOverlay } from '@dnd-kit/core';
import { restrictToWindowEdges } from '@dnd-kit/modifiers';
import EffectLibrary from './components/effect-library';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        console.error('Error caught by boundary:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="alert alert-danger">
                    Something went wrong. Please try refreshing the page.
                </div>
            );
        }
        return this.props.children;
    }
}

const CustomizationApp = ({ story }) => {
    const [activeEffect, setActiveEffect] = React.useState(null);

    const handleDragEnd = (event) => {
        const { active, over } = event;
        
        if (over && active.data.current) {
            const effect = active.data.current;
            const nodeId = over.id.replace('droppable-', '');
            const paragraphIndex = parseInt(nodeId.replace('p', ''));
            
            // Update the node with the new effect
            if (story.paragraphs[paragraphIndex]) {
                story.paragraphs[paragraphIndex].effects = [
                    ...(story.paragraphs[paragraphIndex].effects || []),
                    effect
                ];

                // Update server with new effects
                fetch('/story/update_style', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        paragraphs: story.paragraphs.map((p, idx) => ({
                            index: idx,
                            effects: p.effects || []
                        }))
                    })
                }).catch(error => {
                    console.error('Error updating effects:', error);
                });
            }
        }
        setActiveEffect(null);
    };

    const handleDragStart = (event) => {
        setActiveEffect(event.active.data.current);
    };

    return (
        <DndContext 
            onDragEnd={handleDragEnd}
            onDragStart={handleDragStart}
            modifiers={[restrictToWindowEdges]}
        >
            <div className="customization-wrapper">
                <NodeEditor 
                    story={story}
                    onStyleUpdate={(updatedParagraphs) => {
                        fetch('/story/update_style', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ paragraphs: updatedParagraphs })
                        })
                        .catch(error => {
                            console.error('Error updating style:', error);
                        });
                    }}
                />
                <EffectLibrary />
                <DragOverlay>
                    {activeEffect ? (
                        <div className="effect-item dragging">
                            <span className="effect-icon">{activeEffect.icon}</span>
                            <span className="effect-name">{activeEffect.name}</span>
                        </div>
                    ) : null}
                </DragOverlay>
            </div>
        </DndContext>
    );
};

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('node-editor');
    if (!container) {
        console.error('Node editor container not found');
        return;
    }

    // Parse story data
    let storyData;
    try {
        const storyAttr = container.getAttribute('data-story');
        if (!storyAttr) {
            throw new Error('No story data attribute found');
        }
        storyData = JSON.parse(storyAttr);
        
        // Initialize effects array for each paragraph if not present
        if (storyData.paragraphs) {
            storyData.paragraphs = storyData.paragraphs.map(p => ({
                ...p,
                effects: p.effects || []
            }));
        }
    } catch (error) {
        console.error('Failed to parse story data:', error);
        return;
    }

    // Create root and render with ErrorBoundary
    const root = createRoot(container);
    root.render(
        <ErrorBoundary>
            <CustomizationApp story={storyData} />
        </ErrorBoundary>
    );
});