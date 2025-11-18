import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import workflowService from '../../../../services/workflowService';
import toast from 'react-hot-toast';

/**
 * Custom hook per la gestione della logica principale del WorkflowEditor
 */
export const useWorkflowEditor = ({ 
  workflowId: propWorkflowId, 
  workflowData: propWorkflowData,
  mode = 'edit',
  onClose,
  onSave: onSaveCallback,
  initialWorkflow = null 
}) => {
  console.log('[useWorkflowEditor] Initializing with mode:', mode);
  
  const navigate = useNavigate();
  
  // Stati principali
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
  
  // Stati per configurazione nodi
  const [selectedNode, setSelectedNode] = useState(null);
  const [configFormPosition, setConfigFormPosition] = useState({ x: 0, y: 0 });
  const [showConfigForm, setShowConfigForm] = useState(false);

  // Caricamento iniziale del workflow
  useEffect(() => {
    const initializeWorkflow = async () => {
      try {
        // Se abbiamo workflowData o initialWorkflow, carica direttamente
        if (propWorkflowData) {
          console.log('[useWorkflowEditor] Loading from propWorkflowData:', propWorkflowData);
          await loadWorkflowFromData(propWorkflowData);
          return;
        }

        if (initialWorkflow) {
          console.log('[useWorkflowEditor] Loading from initialWorkflow:', initialWorkflow);
          await loadWorkflowFromData(initialWorkflow);
          return;
        }

        // Se abbiamo un ID, carica il workflow
        if (propWorkflowId) {
          console.log('[useWorkflowEditor] Loading workflow by ID:', propWorkflowId);
          await loadWorkflow(propWorkflowId);
          return;
        }

        console.log('[useWorkflowEditor] No workflow data provided, starting with empty workflow');
      } catch (error) {
        console.error('[useWorkflowEditor] Error initializing workflow:', error);
        toast.error('Errore nel caricamento del workflow');
      }
    };

    initializeWorkflow();
  }, [propWorkflowId, propWorkflowData, initialWorkflow]);

  // Carica workflow da ID
  const loadWorkflow = useCallback(async (workflowId) => {
    if (!workflowId) return;
    
    setIsLoading(true);
    try {
      console.log('[useWorkflowEditor] Loading workflow:', workflowId);
      const workflow = await workflowService.getWorkflow(workflowId);
      await loadWorkflowFromData(workflow);
    } catch (error) {
      console.error('[useWorkflowEditor] Error loading workflow:', error);
      toast.error(`Errore nel caricamento del workflow: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Carica workflow da dati
  const loadWorkflowFromData = useCallback(async (workflowData) => {
    if (!workflowData) return;
    
    console.log('[useWorkflowEditor] Loading workflow data:', workflowData);
    
    setCurrentWorkflow(workflowData);
    setWorkflowName(workflowData.name || '');
    setWorkflowDescription(workflowData.description || '');
    setWorkflowCategory(workflowData.category || 'General');
    setWorkflowTags(workflowData.tags || []);
    
    return workflowData;
  }, []);

  // Funzione di salvataggio
  const saveWorkflow = useCallback(async (nodes, edges) => {
    if (!workflowName.trim()) {
      toast.error('Il nome del workflow è obbligatorio');
      return;
    }

    setIsLoading(true);
    try {
      const workflowData = {
        name: workflowName,
        description: workflowDescription,
        category: workflowCategory,
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
        savedWorkflow = await workflowService.updateWorkflow(currentWorkflow.workflow_id, workflowData);
        toast.success('Workflow aggiornato con successo');
      } else {
        savedWorkflow = await workflowService.createWorkflow(workflowData);
        toast.success('Workflow creato con successo');
      }

      setCurrentWorkflow(savedWorkflow);
      if (onSaveCallback) {
        onSaveCallback(savedWorkflow);
      }
      
      return savedWorkflow;
    } catch (error) {
      console.error('Error saving workflow:', error);
      toast.error('Errore nel salvataggio del workflow');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [workflowName, workflowDescription, workflowCategory, workflowTags, currentWorkflow, onSaveCallback]);

  // Gestione configurazione nodi
  const handleNodeConfigSave = useCallback((nodeId, newConfig) => {
    console.log('[useWorkflowEditor] Saving node config:', nodeId, newConfig);
    return { nodeId, config: newConfig };
  }, []);

  const openNodeConfig = useCallback((node, event) => {
    setSelectedNode(node);
    if (event && event.currentTarget) {
      const rect = event.currentTarget.getBoundingClientRect();
      setConfigFormPosition({
        x: rect.right + 10,
        y: rect.top
      });
    }
    setShowConfigForm(true);
  }, []);

  const closeNodeConfig = useCallback(() => {
    setSelectedNode(null);
    setShowConfigForm(false);
  }, []);

  return {
    // Stati
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
    
    // Setters
    setWorkflowName,
    setWorkflowDescription,
    setWorkflowCategory,
    setWorkflowTags,
    setValidationResult,
    setShowSelectModal,
    setShowTagEditor,
    
    // Funzioni
    loadWorkflow,
    loadWorkflowFromData,
    saveWorkflow,
    handleNodeConfigSave,
    openNodeConfig,
    closeNodeConfig,
    
    // Navigazione
    navigate,
    onClose
  };
};
