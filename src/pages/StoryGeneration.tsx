import React from 'react';
import NodeEditor from '../components/NodeEditor';

const StoryGeneration: React.FC = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Create Your Story</h1>
      <NodeEditor />
    </div>
  );
}

export default StoryGeneration;
