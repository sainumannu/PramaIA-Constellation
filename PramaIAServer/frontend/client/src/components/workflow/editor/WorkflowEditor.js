import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactFlow, {
  useNodesState,
  useEdgesState,
  addEdge,
  Background,
  Controls,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { nodeTypes as baseNodeTypes } from '../nodes';
import { usePDKNodes } from '../nodes/DynamicPDKNodes';
import toast, { Toaster } from 'react-hot-toast';
import workflowService from '../../../services/workflowService';
import WorkflowPalette from './WorkflowPalette';

// Importa le utility e i componenti dalle suddivisioni
import { 
  enrichNodesWithPDKInfo as enrichNodes, 
  getEdgeDataTypeInfo as getEdgeInfo,
  loadWorkflowData as loadData
} from './WorkflowNodeUtility';
import { WorkflowEditorModals } from './WorkflowEditorModals';
import WorkflowEditorHeader from './WorkflowEditorHeader';
import {
  useNodeTypes,
  usePDKNodesEffect,
  useWorkflowLoadEffect,
  useNodeDrop,
  useSaveWorkflow
} from './WorkflowEditorHooks';

// Valori iniziali per nodi ed edges
const emptyNodes = [];
const emptyEdges = [];

/**
 * Componente principale per l\'editor di workflow
 * 
 * @param {Object} props - Proprietà del componente
 * @returns {JSX.Element} - Componente React
 */
const WorkflowEditor = ({ 
  workflowId: propWorkflowId, 
  workflowData: propWorkflowData,
  mode = 'edit',
  onClose,
  onSave: onSaveCallback,
  initialWorkflow = null 
}) => {
  console.log('[WorkflowEditor] Component mounting with mode:', mode);
  console.log('[WorkflowEditor] Props - workflowId:', propWorkflowId, 'workflowData:', propWorkflowData);
  
  // Hook per la navigazione
  const navigate = useNavigate();
  
  // Stati principali
  const [nodes, setNodes, onNodesChange] = useNodesState(emptyNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(emptyEdges);
  const [currentWorkflow, setCurrentWorkflow] = useState(initialWorkflow);
  const [workflowName, setWorkflowName] = useState('');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [workflowCategory, setWorkflowCategory] = useState('General');
  
  // Stati per UI
  const [isLoading, setIsLoading] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [showSelectModal, setShowSelectModal] = useState(false);
  const [showTagEditor, setShowTagEditor] = useState(false);
  const [workflowTags, setWorkflowTags] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [showNodeConfig, setShowNodeConfig] = useState(false);
  const [pdkNodeTypes, setPdkNodeTypes] = useState([]);
  
  // Stati per la visualizzazione delle informazioni sui collegamenti
  const [showEdgeInfoModal, setShowEdgeInfoModal] = useState(false);
  const [selectedEdge, setSelectedEdge] = useState(null);
  
  // Ref per il container React Flow
  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);

  // Hook per i nodi PDK 
  const { fetchNodes } = usePDKNodes();

  // Alias delle funzioni utility per usarle più facilmente
  const enrichNodesWithPDKInfo = useCallback((nodes) => {
    return enrichNodes(nodes, fetchNodes);
  }, [fetchNodes]);
  
  const getEdgeDataTypeInfo = useCallback((edge) => {
    return getEdgeInfo(edge, nodes);
  }, [nodes]);
  
  const loadWorkflowData = useCallback((workflow) => {
    return loadData(
      workflow, 
      setCurrentWorkflow,
      setWorkflowName,
      setWorkflowDescription,
      setWorkflowTags,
      setWorkflowCategory,
      setNodes,
      setEdges,
      enrichNodesWithPDKInfo,
      reactFlowInstance
    );
  }, [enrichNodesWithPDKInfo, reactFlowInstance]);

  // Usa gli hook personalizzati
  const dynamicNodeTypes = useNodeTypes(pdkNodeTypes, baseNodeTypes);
  
  usePDKNodesEffect(fetchNodes, setPdkNodeTypes);

  // Funzione per caricare un workflow
  const loadWorkflow = useCallback(async (workflowId) => {
    console.log('Loading workflow:', workflowId);
    setIsLoading(true);
    try {
      const workflow = await workflowService.getWorkflow(workflowId);
      await loadWorkflowData(workflow);
    } catch (error) {
      console.error('Error loading workflow:', error);
      toast.error(`Errore nel caricamento del workflow: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  }, [loadWorkflowData]);

  useWorkflowLoadEffect(
    propWorkflowId,
    propWorkflowData,
    initialWorkflow,
    loadWorkflowData,
    loadWorkflow
  );

  // Gestione drop di nuovi nodi
  const onDrop = useNodeDrop(
    reactFlowInstance,
    reactFlowWrapper,
    setNodes,
    enrichNodesWithPDKInfo
  );

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

  // Gestione doppio click sui nodi per configurazione
  const onNodeDoubleClick = useCallback((event, node) => {
    console.log('[WorkflowEditor] Node double clicked:', node);
    setSelectedNode(node);
    setShowNodeConfig(true);
  }, []);

  // Gestione doppio click sui collegamenti per visualizzare i tipi di dati
  const onEdgeDoubleClick = useCallback((event, edge) => {
    console.log('[WorkflowEditor] Edge double clicked:', edge);
    setSelectedEdge(edge);
    setShowEdgeInfoModal(true);
  }, []);

  // Funzione di salvataggio
  const saveWorkflow = useSaveWorkflow(
    workflowName,
    workflowDescription,
    workflowCategory,
    nodes,
    edges,
    workflowTags,
    currentWorkflow,
    reactFlowInstance,
    setCurrentWorkflow,
    setIsLoading,
    onSaveCallback,
    workflowService
  );

  // Wrapper per il salvataggio che gestisce i toast
  const handleSaveWorkflow = async () => {
    const result = await saveWorkflow();
    if (result.success) {
      toast.success(result.message);
    } else {
      toast.error(result.error);
    }
  };

  return (
    <div className="h-full flex flex-col bg-white">
      <Toaster position="top-right" />
      
      {/* Header con componente separato */}
      <WorkflowEditorHeader
        currentWorkflow={currentWorkflow}
        workflowName={workflowName}
        workflowDescription={workflowDescription}
        workflowCategory={workflowCategory}
        isLoading={isLoading}
        setWorkflowName={setWorkflowName}
        setWorkflowDescription={setWorkflowDescription}
        setWorkflowCategory={setWorkflowCategory}
        setShowSelectModal={setShowSelectModal}
        setShowTagEditor={setShowTagEditor}
        saveWorkflow={handleSaveWorkflow}
        onClose={onClose}
        onNavigateToList={() => navigate('/app/workflows')}
        reactFlowInstance={reactFlowInstance}
      />
      
      {/* Layout principale */}
      <div className="flex flex-1 h-full">
        {/* Palette laterale */}
        <WorkflowPalette />
        
        {/* Contenitore flessibile per editor e tag editor */}
        <div className="flex-1 flex flex-col">
          {/* Canvas del workflow */}
          <div className="flex-1 relative" ref={reactFlowWrapper}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodesDelete={onNodesDelete}
              onNodeDoubleClick={onNodeDoubleClick}
              onEdgeDoubleClick={onEdgeDoubleClick}
              onInit={setReactFlowInstance}
              onDrop={onDrop}
              onDragOver={onDragOver}
              nodeTypes={dynamicNodeTypes}
              deleteKeyCode="Delete"
              fitViewOnInit={true}
              preventScrolling={false}
              zoomOnScroll={true}
              panOnScroll={false}
              zoomOnDoubleClick={false}
              minZoom={0.1}
              maxZoom={2}
              // Impostazioni per consentire coordinate negative e grandi spazi di lavoro
              translateExtent={[
                [-2000, -2000], // Valori min X e Y
                [2000, 2000]   // Valori max X e Y
              ]}
              defaultViewport={{ x: 0, y: 0, zoom: 1 }}
            >
              <Background />
              <Controls />
            </ReactFlow>
          </div>
        </div>
      </div>

      {/* Modali dell\'editor di workflow */}
      <WorkflowEditorModals
        showSelectModal={showSelectModal}
        showTagEditor={showTagEditor}
        showNodeConfig={showNodeConfig}
        showEdgeInfoModal={showEdgeInfoModal}
        workflowTags={workflowTags}
        selectedNode={selectedNode}
        selectedEdge={selectedEdge}
        setShowSelectModal={setShowSelectModal}
        setShowTagEditor={setShowTagEditor}
        setShowNodeConfig={setShowNodeConfig}
        setShowEdgeInfoModal={setShowEdgeInfoModal}
        setWorkflowTags={setWorkflowTags}
        setNodes={setNodes}
        loadWorkflow={loadWorkflow}
        removeNode={removeNode}
        getEdgeDataTypeInfo={getEdgeDataTypeInfo}
        nodes={nodes}
      />
    </div>
  );
};

export default WorkflowEditor;
