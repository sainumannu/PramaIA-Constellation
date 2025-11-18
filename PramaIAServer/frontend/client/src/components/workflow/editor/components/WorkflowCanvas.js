import React, { useEffect } from 'react';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';

/**
 * Componente canvas ReactFlow separato
 */
const WorkflowCanvas = ({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onConnect,
  onNodesDelete,
  onInit,
  onDrop,
  onDragOver,
  onNodeDoubleClick,
  nodeTypes,
  reactFlowWrapper,
  className = "flex-1 relative"
}) => {
  // Debug: monitora i nodi ricevuti dal canvas
  useEffect(() => {
    console.log('[WorkflowCanvas] Received nodes:', nodes);
    console.log('[WorkflowCanvas] Received edges:', edges);
    console.log('[WorkflowCanvas] NodeTypes:', Object.keys(nodeTypes || {}));
  }, [nodes, edges, nodeTypes]);

  return (
    <div className={className} ref={reactFlowWrapper}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodesDelete={onNodesDelete}
        onInit={onInit}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onNodeDoubleClick={onNodeDoubleClick}
        nodeTypes={nodeTypes}
        deleteKeyCode="Delete"
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
};

export default WorkflowCanvas;
