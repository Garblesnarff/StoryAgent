import React from 'react';
import { useDraggable } from '@dnd-kit/core';

const EffectItem = ({ effect }) => {
    const { attributes, listeners, setNodeRef, transform } = useDraggable({
        id: `effect-${effect.id}`,
        data: effect
    });

    const style = transform ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
    } : undefined;

    return (
        <div 
            ref={setNodeRef} 
            {...listeners} 
            {...attributes}
            className="effect-item"
            style={style}
        >
            <div className="effect-icon">{effect.icon}</div>
            <div className="effect-name">{effect.name}</div>
            <div className="effect-description">{effect.description}</div>
        </div>
    );
};

const EffectLibrary = () => {
    const effects = [
        {
            id: 'highlight',
            name: 'Highlight',
            description: 'Emphasize key moments',
            icon: '✨',
            type: 'emphasis'
        },
        {
            id: 'dramatic',
            name: 'Dramatic Pause',
            description: 'Add suspense',
            icon: '🎭',
            type: 'pacing'
        },
        {
            id: 'atmosphere',
            name: 'Atmosphere',
            description: 'Set the mood',
            icon: '🌟',
            type: 'mood'
        },
        {
            id: 'transition',
            name: 'Transition',
            description: 'Smooth scene changes',
            icon: '🔄',
            type: 'flow'
        }
    ];

    return (
        <div className="effect-library">
            <div className="effect-library-header">
                <h3>Effect Library</h3>
                <p>Drag effects to enhance your story</p>
            </div>
            <div className="effect-list">
                {effects.map(effect => (
                    <EffectItem key={effect.id} effect={effect} />
                ))}
            </div>
        </div>
    );
};

export default EffectLibrary;
