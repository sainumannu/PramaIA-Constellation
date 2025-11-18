import React from 'react';
import { Toaster } from 'react-hot-toast';

const WorkflowEditor = ({ workflowData, onSave, onLoad, onExecute }) => {
  return (
    <div className="flex h-full">
      <div className="flex-1 p-4">
        <h1 className="text-2xl font-bold mb-4">Workflow Editor</h1>
        <p>Editor workflow in sviluppo...</p>
        
        <div className="mt-4">
          <p><strong>Props ricevute:</strong></p>
          <pre className="bg-gray-100 p-2 rounded text-sm">
            {JSON.stringify({ 
              hasWorkflowData: !!workflowData,
              hasSave: typeof onSave === 'function',
              hasLoad: typeof onLoad === 'function',
              hasExecute: typeof onExecute === 'function'
            }, null, 2)}
          </pre>
        </div>
      </div>
      
      <Toaster position="bottom-right" />
    </div>
  );
};

export default WorkflowEditor;
