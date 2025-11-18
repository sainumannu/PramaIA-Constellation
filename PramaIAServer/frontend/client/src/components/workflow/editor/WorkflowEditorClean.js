import React, { useState, useCallback, useRef, useEffect } from 'react';
import ReactFlow, {
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  ReactFlowProvider,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { nodeTypes } from '../nodes';
import toast, { Toaster } from 'react-hot-toast';
import workflowService from '../../../services/workflowService';
import WorkflowToolbar from './WorkflowToolbar';
import WorkflowSelectModal from '../../WorkflowSelectModal';
import TagEditor from '../../TagEditor';
import ValidationPanel from '../../ValidationPanel';
import WorkflowPalette from './WorkflowPalette';

// Initial empty state for new workflows
const emptyNodes = [];
const emptyEdges = [];

const WorkflowEditor = ({ 
  workflowId: propWorkflowId, 
  mode = 'edit',
  onClose,
  onSave: onSaveCallback,
  initialWorkflow = null 
}) => {
  console.log('[WorkflowEditor] Component mounting with mode:', mode);
  
  // Stati principali
  const [nodes, setNodes, onNodesChange] = useNodesState(emptyNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(emptyEdges);
  const [currentWorkflow, setCurrentWorkflow] = useState(initialWorkflow);
  const [workflowName, setWorkflowName] = useState('');
  const [workflowDescription, setWorkflowDescription] = useState('');
  
  // Stati per UI
  const [isLoading, setIsLoading] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [showSelectModal, setShowSelectModal] = useState(false);
  const [showTagEditor, setShowTagEditor] = useState(false);
  const [workflowTags, setWorkflowTags] = useState([]);
  
  // Ref per il container React Flow
  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);

  // Caricamento workflow se specificato
  useEffect(() => {
    if (propWorkflowId && propWorkflowId !== 'new') {
      loadWorkflow(propWorkflowId);
    }
  }, [propWorkflowId]);

  // Funzione per caricare un workflow
  const loadWorkflow = async (workflowId) => {
    console.log('Loading workflow:', workflowId);
    setIsLoading(true);
    try {
      const workflow = await workflowService.getWorkflow(workflowId);
      setCurrentWorkflow(workflow);
      setWorkflowName(workflow.name);
      setWorkflowDescription(workflow.description || '');
      setWorkflowTags(workflow.tags || []);
      
      console.log('Loading nodes into editor:', workflow.nodes);
      const loadedNodes = workflow.nodes.map(node => ({
        id: node.node_id,
        type: node.node_type,
        position: { x: node.position?.x || 100, y: node.position?.y || 100 },
        data: { 
          name: node.name,
          description: node.description,
          config: node.config 
        }
      }));
      
      const loadedEdges = workflow.connections.map(conn => ({
        id: `${conn.source_node}-${conn.target_node}`,
        source: conn.source_node,
        target: conn.target_node,
        sourceHandle: conn.source_output,
        targetHandle: conn.target_input,
        type: 'default'
      }));
      
      setNodes(loadedNodes);
      setEdges(loadedEdges);
      
      toast.success(`Workflow "${workflow.name}" caricato`);
    } catch (error) {
      console.error('Error loading workflow:', error);
      toast.error('Errore nel caricamento del workflow');
    } finally {
      setIsLoading(false);
    }
  };

  // Gestione drop di nuovi nodi
  const onDrop = useCallback((event) => {
    event.preventDefault();
    
    const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
    const type = event.dataTransfer.getData('application/reactflow');
    const nodeDefinition = JSON.parse(event.dataTransfer.getData('nodeDefinition') || '{}');
    
    if (typeof type === 'undefined' || !type) {
      return;
    }
    
    const position = reactFlowInstance.project({
      x: event.clientX - reactFlowBounds.left,
      y: event.clientY - reactFlowBounds.top,
    });
    
    const newNode = {
      id: `${type}_${Date.now()}`,
      type,
      position,
      data: {
        name: nodeDefinition.label || type,
        description: nodeDefinition.description || '',
        config: nodeDefinition.defaultConfig || {}
      }
    };
    
    setNodes((nds) => nds.concat(newNode));
  }, [reactFlowInstance, setNodes]);

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onConnect = useCallback((params) => {
    setEdges((eds) => addEdge(params, eds));
  }, [setEdges]);

  // Funzione per rimuovere un nodo (chiamata dal pulsante delete nel PDKNode)
  const removeNode = useCallback((nodeId) => {
    console.log('[WorkflowEditor] Removing node:', nodeId);
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
    toast.success('Nodo rimosso');
  }, [setNodes, setEdges]);

  // Gestione eliminazione nodi con tasto delete
  const onNodesDelete = useCallback((nodesToDelete) => {
    const nodeIds = nodesToDelete.map(node => node.id);
    setNodes((nds) => nds.filter((node) => !nodeIds.includes(node.id)));
    setEdges((eds) => eds.filter((edge) => !nodeIds.includes(edge.source) && !nodeIds.includes(edge.target)));
    toast.success(`${nodeIds.length} nodo/i eliminato/i`);
  }, [setNodes, setEdges]);

  // Rendi la funzione removeNode disponibile globalmente per PDKNode
  useEffect(() => {
    window.removeNode = removeNode;
    return () => {
      delete window.removeNode;
    };
  }, [removeNode]);

  // Funzione di salvataggio con protezione da doppi click
  const saveWorkflow = async () => {
    if (!workflowName.trim()) {
      toast.error('Il nome del workflow è obbligatorio');
      return;
    }

    // Protezione da doppi click durante il salvataggio
    if (isLoading) {
      console.warn('[WorkflowEditor] Save already in progress, ignoring duplicate request');
      return;
    }

    setIsLoading(true);
    try {
      const workflowData = {
        name: workflowName,
        description: workflowDescription,
        nodes: nodes.map(node => ({
          node_id: node.id,
          node_type: node.type,
          name: node.data.name,
          description: node.data.description,
          config: node.data.config,
          position: node.position,
          icon: node.data.icon,     // BUGFIX: Preserva l'icona del nodo durante il salvataggio
          color: node.data.color    // BUGFIX: Preserva il colore del nodo durante il salvataggio
        })),
        connections: edges.map(edge => ({
          source_node: edge.source,
          target_node: edge.target,
          source_output: edge.sourceHandle,
          target_input: edge.targetHandle
        })),
        tags: workflowTags
      };

      let savedWorkflow;
      if (currentWorkflow?.workflow_id) {
        console.log('[WorkflowEditor] Updating workflow:', currentWorkflow.workflow_id);
        savedWorkflow = await workflowService.updateWorkflow(currentWorkflow.workflow_id, workflowData);
        toast.success('Workflow aggiornato con successo');
      } else {
        console.log('[WorkflowEditor] Creating new workflow:', workflowName);
        savedWorkflow = await workflowService.createWorkflow(workflowData);
        toast.success('Workflow creato con successo');
      }

      setCurrentWorkflow(savedWorkflow);
      if (onSaveCallback) {
        onSaveCallback(savedWorkflow);
      }
    } catch (error) {
      console.error('Error saving workflow:', error);
      const errorMessage = error?.message || 'Errore nel salvataggio del workflow';
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-white">
      <Toaster position="top-right" />
      
      {/* Header semplificato */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {currentWorkflow ? `Modifica: ${currentWorkflow.name}` : 'Nuovo Workflow'}
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              {currentWorkflow ? 'Modifica il workflow esistente' : 'Crea un nuovo workflow trascinando i nodi dalla palette'}
            </p>
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={() => setShowSelectModal(true)}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              Carica
            </button>
            <button
              onClick={() => setShowTagEditor(true)}
              className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600"
            >
              Tags
            </button>
            <button
              onClick={saveWorkflow}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            >
              {isLoading ? 'Salvando...' : 'Salva'}
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                Chiudi
              </button>
            )}
          </div>
        </div>
        
        {/* Campi nome e descrizione */}
        <div className="mt-4 grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nome Workflow
            </label>
            <input
              type="text"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="Inserisci il nome del workflow"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descrizione
            </label>
            <input
              type="text"
              value={workflowDescription}
              onChange={(e) => setWorkflowDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="Descrizione opzionale"
            />
          </div>
        </div>
      </div>
      
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
          <div className="flex-1 relative" ref={reactFlowWrapper}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodesDelete={onNodesDelete}
              onInit={setReactFlowInstance}
              onDrop={onDrop}
              onDragOver={onDragOver}
              nodeTypes={nodeTypes}
              deleteKeyCode="Delete"
              fitView
            >
              <Background />
              <Controls />
            </ReactFlow>
          </div>
        </div>
      </div>

      {/* Modali */}
      {showSelectModal && (
        <WorkflowSelectModal
          onSelect={(workflow) => {
            loadWorkflow(workflow.workflow_id);
            setShowSelectModal(false);
          }}
          onClose={() => setShowSelectModal(false)}
        />
      )}
      
      {showTagEditor && (
        <TagEditor
          tags={workflowTags}
          onSave={(tags) => {
            setWorkflowTags(tags);
            setShowTagEditor(false);
          }}
          onClose={() => setShowTagEditor(false)}
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
