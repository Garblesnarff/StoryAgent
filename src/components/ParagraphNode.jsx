import React from 'react';

const ParagraphNode = ({ data }) => {
  return (
    <div className="paragraph-node">
      <div className="node-header">Paragraph {data.index + 1}</div>
      <div className="node-content">
        <p>{data.text.substring(0, 100)}...</p>
        <div className="node-controls">
          <select 
            value={data.imageStyle || 'realistic'} 
            onChange={(e) => data.onStyleChange(data.index, 'image', e.target.value)}
          >
            <option value="realistic">Realistic</option>
            <option value="artistic">Artistic</option>
            <option value="cartoon">Cartoon</option>
          </select>
          <select 
            value={data.voiceStyle || 'neutral'} 
            onChange={(e) => data.onStyleChange(data.index, 'voice', e.target.value)}
          >
            <option value="neutral">Neutral</option>
            <option value="dramatic">Dramatic</option>
            <option value="cheerful">Cheerful</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default ParagraphNode;
