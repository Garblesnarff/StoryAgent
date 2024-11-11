import React from 'react';

const effects = [
  { id: 'realistic', label: 'Realistic', category: 'image' },
  { id: 'artistic', label: 'Artistic', category: 'image' },
  { id: 'cartoon', label: 'Cartoon', category: 'image' },
  { id: 'neutral', label: 'Neutral', category: 'voice' },
  { id: 'cheerful', label: 'Cheerful', category: 'voice' },
  { id: 'dramatic', label: 'Dramatic', category: 'voice' }
];

const LibraryPanel = () => {
  const onDragStart = (event, effect) => {
    event.dataTransfer.setData('application/json', JSON.stringify(effect));
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <aside className="library-panel">
      <div className="library-header">Effects Library</div>
      <div className="effects-container">
        <div className="effect-category">
          <h3>Image Styles</h3>
          {effects
            .filter(effect => effect.category === 'image')
            .map(effect => (
              <div
                key={effect.id}
                className="effect-item"
                draggable
                onDragStart={(e) => onDragStart(e, effect)}
              >
                {effect.label}
              </div>
            ))}
        </div>
        <div className="effect-category">
          <h3>Voice Styles</h3>
          {effects
            .filter(effect => effect.category === 'voice')
            .map(effect => (
              <div
                key={effect.id}
                className="effect-item"
                draggable
                onDragStart={(e) => onDragStart(e, effect)}
              >
                {effect.label}
              </div>
            ))}
        </div>
      </div>
    </aside>
  );
};

export default LibraryPanel;
