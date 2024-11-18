import React from 'react';

const effects = [
    {
        id: 'image_filter',
        type: 'image',
        label: 'Image Filter',
        options: [
            { value: 'vintage', label: 'Vintage' },
            { value: 'noir', label: 'Film Noir' },
            { value: 'fantasy', label: 'Fantasy' }
        ]
    },
    {
        id: 'text_enhancement',
        type: 'text',
        label: 'Text Enhancement',
        options: [
            { value: 'dramatic', label: 'Dramatic' },
            { value: 'poetic', label: 'Poetic' },
            { value: 'descriptive', label: 'Descriptive' }
        ]
    },
    {
        id: 'mood_enhancement',
        type: 'mood',
        label: 'Mood Enhancement',
        options: [
            { value: 'happy', label: 'Happy' },
            { value: 'mysterious', label: 'Mysterious' },
            { value: 'suspenseful', label: 'Suspenseful' }
        ]
    }
];

const EffectPanel = () => {
    const handleDragStart = (e, effect) => {
        e.dataTransfer.setData('application/reactflow', JSON.stringify(effect));
        e.dataTransfer.effectAllowed = 'move';
    };

    return (
        <div className="effect-panel">
            <div className="effect-panel-header">
                Effects Library
            </div>
            <div className="effect-list">
                {effects.map((effect) => (
                    <div
                        key={effect.id}
                        className="effect-item"
                        draggable
                        onDragStart={(e) => handleDragStart(e, effect)}
                    >
                        <div className="effect-item-header">
                            {effect.label}
                        </div>
                        <div className="effect-item-options">
                            {effect.options.map((opt) => (
                                <div key={opt.value} className="effect-option">
                                    {opt.label}
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default EffectPanel;
