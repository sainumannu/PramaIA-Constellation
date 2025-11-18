import React, { useState } from 'react';
import { Toaster } from 'react-hot-toast';

// Test progressivo per identificare il problema

// Test 1: Solo React Flow base
import ReactFlow, {
  ReactFlowProvider,
  Controls,
  Background,
  MiniMap
} from 'reactflow';
import 'reactflow/dist/style.css';

const WorkflowEditorTest = ({ workflowData, onSave, onLoad, onExecute }) => {
  const [nodes] = useState([]);
  const [edges] = useState([]);

  return (
    <div className="flex h-full">
      <div className="flex-1">
        <div className="h-full">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
          >
            <Controls />
            <Background variant="dots" gap={12} size={1} />
            <MiniMap />
          </ReactFlow>
        </div>
      </div>
      
      <Toaster position="bottom-right" />
    </div>
  );
};

// Wrapper con provider
const WorkflowEditorTestWrapper = (props) => (
  <ReactFlowProvider>
    <WorkflowEditorTest {...props} />
  </ReactFlowProvider>
);

export default WorkflowEditorTestWrapper;
