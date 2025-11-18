import React, { useEffect } from 'react';
import { ReactFlowProvider } from 'reactflow';
import toast, { Toaster } from 'react-hot-toast';

import { useWorkflowEditor } from './hooks/useWorkflowEditor';
import { useWorkflowCanvas } from './hooks/useWorkflowCanvas';
import WorkflowHeader from './components/WorkflowHeader';
import WorkflowCanvas from './components/WorkflowCanvas';
import WorkflowPalette from './WorkflowPalette';
import WorkflowSelectModal from '../../WorkflowSelectModal';
import TagEditor from '../../TagEditor';
import ValidationPanel from '../../ValidationPanel';
import NodeConfigForm from './NodeConfigForm';

/**
 * WorkflowEditor refactorizzato - Componente principale
 */
const WorkflowEditor = (props) => {
  console.log('[WorkflowEditor] Component mounting with props:', props);
  
  // Hook per la logica principale
  const {
    currentWorkflow,
    workflowName,
    workflowDescription,
    workflowCategory,
    workflowTags,
    isLoading,
    validationResult,
    showSelectModal,
    showTagEditor,
    selectedNode,
    configFormPosition,
    showConfigForm,
    setWorkflowName,
    setWorkflowDescription,
    setWorkflowCategory,
    setWorkflowTags,
    setValidationResult,
    setShowSelectModal,
    setShowTagEditor,
    loadWorkflow,
    loadWorkflowFromData,
    saveWorkflow,
    handleNodeConfigSave,
    openNodeConfig,
    closeNodeConfig,
    navigate,
    onClose
  } = useWorkflowEditor(props);

  // Hook per la gestione del canvas
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    reactFlowWrapper,
    reactFlowInstance,
    setReactFlowInstance,
    dynamicNodeTypes,
    onDrop,
    onDragOver,
    onConnect,
    onNodesDelete,
    loadWorkflowIntoCanvas,
    updateNodeConfig,
    pdkNodes,
    pdkLoading
  } = useWorkflowCanvas();

  // Sincronizza il caricamento del workflow nel canvas - aspetta che i nodi PDK siano caricati
  useEffect(() => {
    console.log('[WorkflowEditorRefactored] useEffect - currentWorkflow changed:', currentWorkflow);
    console.log('[WorkflowEditorRefactored] PDK loading status:', pdkLoading, 'PDK nodes available:', pdkNodes?.length || 0);
    
    if (currentWorkflow && !pdkLoading) {
      console.log('[WorkflowEditorRefactored] Loading workflow into canvas...');
      loadWorkflowIntoCanvas(currentWorkflow);
    }
  }, [currentWorkflow, loadWorkflowIntoCanvas, pdkLoading]);

  // Gestori eventi
  const handleSave = async () => {
    try {
      await saveWorkflow(nodes, edges);
    } catch (error) {
      console.error('[WorkflowEditor] Save error:', error);
    }
  };

  const handleLoadWorkflow = async (workflowId) => {
    try {
      await loadWorkflow(workflowId);
      setShowSelectModal(false);
    } catch (error) {
      console.error('[WorkflowEditor] Load error:', error);
    }
  };

  const handleWorkflowSelect = async (workflow) => {
    try {
      await loadWorkflowFromData(workflow);
      setShowSelectModal(false);
    } catch (error) {
      console.error('[WorkflowEditor] Select error:', error);
    }
  };

  const handleNodeConfigSaveInternal = (nodeId, newConfig) => {
    updateNodeConfig(nodeId, newConfig);
    handleNodeConfigSave(nodeId, newConfig);
    closeNodeConfig();
  };

  const handleTagsSave = (tags) => {
    setWorkflowTags(tags);
    setShowTagEditor(false);
  };

  // Gestione doppio click sui nodi per configurazione
  const onNodeDoubleClick = (event, node) => {
    console.log('[WorkflowEditor] Node double-clicked:', node);
    openNodeConfig(node, event);
  };

  return (
    <div className="h-full flex flex-col bg-white">
      <Toaster position="top-right" />
      
      {/* Header */}
      <WorkflowHeader
        currentWorkflow={currentWorkflow}
        workflowName={workflowName}
        workflowDescription={workflowDescription}
        workflowCategory={workflowCategory}
        isLoading={isLoading}
        reactFlowInstance={reactFlowInstance}
        onWorkflowNameChange={setWorkflowName}
        onWorkflowDescriptionChange={setWorkflowDescription}
        onWorkflowCategoryChange={setWorkflowCategory}
        onSave={handleSave}
        onLoad={() => setShowSelectModal(true)}
        onClose={onClose}
        onShowTagEditor={() => setShowTagEditor(true)}
        onNavigateToList={() => navigate('/app/workflows')}
      />
      
      {/* Layout principale */}
      <div className="flex flex-1 h-full gap-4">
        {/* Palette laterale */}
        <WorkflowPalette />

        {/* Editor principale + ValidationPanel */}
        <div className="flex-1 relative flex flex-col">
          <div className="mb-2">
            <ValidationPanel
              workflow={{
                name: workflowName,
                description: workflowDescription,
                nodes: nodes.map(n => ({
                  ...n.data,
                  node_id: n.id,
                  node_type: n.type,
                  position: n.position
                })),
                connections: edges.map(e => ({
                  source_node: e.source,
                  target_node: e.target,
                  source_output: e.sourceHandle,
                  target_input: e.targetHandle
                }))
              }}
              onValidationChange={setValidationResult}
              isVisible={true}
            />
          </div>
          
          {/* Canvas */}
          <WorkflowCanvas
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodesDelete={onNodesDelete}
            onInit={setReactFlowInstance}
            onDrop={onDrop}
            onDragOver={onDragOver}
            nodeTypes={dynamicNodeTypes}
            reactFlowWrapper={reactFlowWrapper}
            onNodeDoubleClick={onNodeDoubleClick}
          />
        </div>
      </div>

      {/* Modali */}
      {showSelectModal && (
        <WorkflowSelectModal
          onSelect={handleWorkflowSelect}
          onClose={() => setShowSelectModal(false)}
        />
      )}
      
      {showTagEditor && (
        <TagEditor
          tags={workflowTags}
          onSave={handleTagsSave}
          onClose={() => setShowTagEditor(false)}
        />
      )}

      {/* Form configurazione nodo */}
      {showConfigForm && selectedNode && (
        <NodeConfigForm
          node={selectedNode}
          position={configFormPosition}
          onSave={handleNodeConfigSaveInternal}
          onClose={closeNodeConfig}
        />
      )}
    </div>
  );
};

// Wrapper con provider
const WorkflowEditorWrapper = (props) => (
  <ReactFlowProvider>
    <WorkflowEditor {...props} />
  </ReactFlowProvider>
);

export default WorkflowEditorWrapper;
