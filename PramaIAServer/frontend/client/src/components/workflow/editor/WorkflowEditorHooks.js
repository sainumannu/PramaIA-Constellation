import { useMemo, useCallback, useEffect } from 'react';
import PDKNode from '../nodes/PDKNode';

/**
 * Hook per gestire i tipi di nodo dinamici
 * 
 * @param {Array} pdkNodeTypes - Tipi di nodi PDK disponibili
 * @param {Object} baseNodeTypes - Tipi di nodo base predefiniti
 * @returns {Object} - Tipi di nodo combinati
 */
export const useNodeTypes = (pdkNodeTypes, baseNodeTypes) => {
  return useMemo(() => {
    console.log('[WorkflowEditor] Rebuilding dynamicNodeTypes with pdkNodeTypes:', pdkNodeTypes);
    const newNodeTypes = { ...baseNodeTypes };
    
    // Lista di tutti i nodi PDK conosciuti dal server
    const knownPDKNodes = [
      'text_joiner', 'text_filter', 'user_context_provider',
      'pdf_input_node', 'pdf_text_extractor', 'text_chunker', 
      'text_embedder', 'chroma_vector_store', 'query_input_node',
      'chroma_retriever', 'llm_processor', 'pdf_results_formatter'
    ];
    
    // Registra tutti i nodi PDK conosciuti
    knownPDKNodes.forEach(nodeType => {
      console.log(`[WorkflowEditor] Registering known PDK node type: "${nodeType}"`);
      newNodeTypes[nodeType] = PDKNode;
    });
    
    // Registra anche eventuali tipi aggiuntivi dal pdkNodeTypes
    if (pdkNodeTypes && pdkNodeTypes.length > 0) {
      pdkNodeTypes.forEach(nodeType => {
        if (!newNodeTypes[nodeType]) {
          console.log(`[WorkflowEditor] Registering additional PDK node type: "${nodeType}"`);
          newNodeTypes[nodeType] = PDKNode;
        }
      });
    }
    
    console.log('[WorkflowEditor] Final registered node types:', Object.keys(newNodeTypes));
    return newNodeTypes;
  }, [pdkNodeTypes, baseNodeTypes]);
};

/**
 * Hook per caricare i nodi PDK
 * 
 * @param {Function} fetchNodes - Funzione per recuperare i nodi
 * @param {Function} setPdkNodeTypes - Funzione per impostare i tipi di nodo
 */
export const usePDKNodesEffect = (fetchNodes, setPdkNodeTypes) => {
  useEffect(() => {
    // Usiamo un ID univoco per tracciare questa istanza dell'effetto
    const effectId = Math.random().toString(36).substring(2, 8);
    console.log(`[WorkflowEditor] PDK nodes effect starting (ID: ${effectId})...`);
    
    let isMounted = true; // Flag per prevenire aggiornamenti su componenti smontati
    let retryCount = 0;
    const maxRetries = 1; // Ridotto a 1 solo tentativo per evitare registrazioni multiple
    
    const loadPDKNodes = async (forceRefresh = false) => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          console.error('[WorkflowEditor] No token available, cannot load PDK nodes');
          return;
        }
        
        console.log(`[WorkflowEditor] Loading PDK nodes (Effect ID: ${effectId}, Attempt: ${retryCount + 1})...`);
        console.log('[WorkflowEditor] Calling fetchNodes to load PDK nodes...');
        // Usiamo il sistema di cache da DynamicPDKNodes.js
        const pdkNodes = await fetchNodes(forceRefresh);
        
        // Previene aggiornamenti se il componente è stato smontato
        if (!isMounted) {
          console.log(`[WorkflowEditor] Component unmounted, ignoring PDK nodes update (Effect ID: ${effectId})`);
          return;
        }
        
        // Verifica se abbiamo ricevuto nodi validi
        if (!pdkNodes || pdkNodes.length === 0) {
          console.warn(`[WorkflowEditor] No PDK nodes received (Effect ID: ${effectId})`);
          return;
        }
        
        // Estrae solo i tipi di nodo per la memoizzazione
        const nodeTypesList = pdkNodes.map(node => node.type);
        
        console.log(`[WorkflowEditor] PDK nodes received:`, pdkNodes);
        console.log(`[WorkflowEditor] PDK node types registered (Effect ID: ${effectId}):`, nodeTypesList);
        
        setPdkNodeTypes(nodeTypesList);
        
      } catch (error) {
        console.error(`[WorkflowEditor] Error loading PDK nodes (Effect ID: ${effectId}):`, error);
        
        // Riprova una sola volta dopo un errore
        if (retryCount < maxRetries) {
          retryCount++;
          console.log(`[WorkflowEditor] Retrying PDK nodes load (Effect ID: ${effectId}, Attempt: ${retryCount + 1})...`);
          setTimeout(() => loadPDKNodes(true), 1000); // Ritenta con forceRefresh=true
        } else {
          console.error(`[WorkflowEditor] Maximum retry attempts reached (Effect ID: ${effectId})`);
        }
      }
    };
    
    loadPDKNodes(false); // Inizia senza forzare refresh, usa la cache se disponibile
    
    // Funzione di cleanup
    return () => {
      console.log(`[WorkflowEditor] PDK nodes effect cleanup (ID: ${effectId})`);
      isMounted = false;
    };
  }, [fetchNodes, setPdkNodeTypes]); 
};

/**
 * Hook per gestire il caricamento del workflow
 * 
 * @param {string|null} propWorkflowId - ID del workflow da caricare
 * @param {Object|null} propWorkflowData - Dati del workflow
 * @param {Object|null} initialWorkflow - Workflow iniziale
 * @param {Function} loadWorkflowData - Funzione per caricare i dati
 * @param {Function} loadWorkflow - Funzione per caricare un workflow
 */
export const useWorkflowLoadEffect = (
  propWorkflowId, 
  propWorkflowData, 
  initialWorkflow, 
  loadWorkflowData,
  loadWorkflow
) => {
  useEffect(() => {
    console.log('[WorkflowEditor] useEffect - propWorkflowId:', propWorkflowId, 'propWorkflowData:', propWorkflowData);
    
    const loadInitialWorkflow = async () => {
      try {
        if (propWorkflowData) {
          console.log('[WorkflowEditor] Loading workflow from props data:', propWorkflowData);
          loadWorkflowData(propWorkflowData);
        } else if (propWorkflowId) {
          console.log('[WorkflowEditor] Loading workflow by ID:', propWorkflowId);
          loadWorkflow(propWorkflowId);
        } else if (initialWorkflow) {
          console.log('[WorkflowEditor] Loading initial workflow:', initialWorkflow);
          loadWorkflowData(initialWorkflow);
        } else {
          console.log('[WorkflowEditor] No workflow to load, starting empty');
        }
      } catch (error) {
        console.error('[WorkflowEditor] Error loading initial workflow:', error);
        // Gestito da chi chiama il hook
      }
    };
    
    loadInitialWorkflow();
  }, [propWorkflowId, propWorkflowData, initialWorkflow, loadWorkflowData, loadWorkflow]);
};

/**
 * Hook per gestire il drop di elementi sul canvas
 * 
 * @param {Object} reactFlowInstance - Istanza di ReactFlow
 * @param {Object} reactFlowWrapper - Ref del wrapper ReactFlow
 * @param {Function} setNodes - Funzione per aggiornare i nodi
 * @param {Function} enrichNodesWithPDKInfo - Funzione per arricchire i nodi
 * @returns {Function} - Funzione di gestione drop
 */
export const useNodeDrop = (reactFlowInstance, reactFlowWrapper, setNodes, enrichNodesWithPDKInfo) => {
  return useCallback(async (event) => {
    event.preventDefault();
    
    const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
    const type = event.dataTransfer.getData('application/reactflow');
    const nodeDefinition = JSON.parse(event.dataTransfer.getData('nodeDefinition') || '{}');
    
    console.log('[WorkflowEditor] Drop event - type:', type);
    console.log('[WorkflowEditor] Drop event - nodeDefinition:', nodeDefinition);
    
    if (typeof type === 'undefined' || !type) {
      console.log('[WorkflowEditor] Drop cancelled - no type');
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
        name: nodeDefinition.label || nodeDefinition.name || type,
        description: nodeDefinition.description || '',
        config: nodeDefinition.defaultConfig || {},
        // Include schema di configurazione per nodi PDK
        configSchema: nodeDefinition.configSchema || null,
        // Mantieni metadati PDK se presenti
        ...(nodeDefinition.pluginId && {
          pluginId: nodeDefinition.pluginId,
          pluginName: nodeDefinition.pluginName,
          pluginVersion: nodeDefinition.pluginVersion
        })
      }
    };
    
    console.log('[WorkflowEditor] Creating new node:', newNode);
    
    // 🎯 GESTIONE ICONA PDK: Preserva l'icona dalla palette se è valida
    console.log('[WorkflowEditor] 🎨 Checking if dropped node has valid icon from palette...');
    console.log('[WorkflowEditor] nodeDefinition.icon:', nodeDefinition.icon);
    
    // Se il nodo ha già un'icona valida dalla palette, la usiamo direttamente
    const hasValidPaletteIcon = nodeDefinition.icon && 
                               !nodeDefinition.icon.includes('?') && 
                               !nodeDefinition.icon.includes('�') &&
                               nodeDefinition.icon !== '🧩'; // Non è l'icona di default
    
    if (hasValidPaletteIcon) {
      console.log('[WorkflowEditor] ✅ Using valid icon from palette:', nodeDefinition.icon);
      // Aggiungi direttamente i data dalla palette senza enrichment
      newNode.data.icon = nodeDefinition.icon;
      newNode.data.color = '#ffffff';
      setNodes((nds) => nds.concat(newNode));
    } else {
      console.log('[WorkflowEditor] 🎨 No valid palette icon, enriching with PDK data...');
      try {
        const enrichedNodes = await enrichNodesWithPDKInfo([newNode]);
        const enrichedNode = enrichedNodes[0];
        console.log('[WorkflowEditor] 🎨 Enriched dropped node:', enrichedNode);
        
        setNodes((nds) => nds.concat(enrichedNode));
      } catch (error) {
        console.error('[WorkflowEditor] Error enriching dropped node:', error);
        // Fallback: aggiungi il nodo senza arricchimento
        setNodes((nds) => nds.concat(newNode));
      }
    }
  }, [reactFlowInstance, reactFlowWrapper, setNodes, enrichNodesWithPDKInfo]);
};

/**
 * Hook per gestire il salvataggio del workflow
 * 
 * @param {string} workflowName - Nome del workflow
 * @param {string} workflowDescription - Descrizione
 * @param {string} workflowCategory - Categoria
 * @param {Array} nodes - Nodi del workflow
 * @param {Array} edges - Collegamenti tra nodi
 * @param {Array} workflowTags - Tag del workflow
 * @param {Object} currentWorkflow - Workflow corrente
 * @param {Object} reactFlowInstance - Istanza ReactFlow
 * @param {Function} setCurrentWorkflow - Aggiorna il workflow corrente
 * @param {Function} setIsLoading - Aggiorna lo stato di caricamento
 * @param {Function} onSaveCallback - Callback dopo il salvataggio
 * @returns {Function} - Funzione di salvataggio
 */
export const useSaveWorkflow = (
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
) => {
  const saveWorkflow = useCallback(async () => {
    console.log('🔴 useSaveWorkflow CALLED');
    
    if (!workflowName.trim()) {
      return { success: false, error: 'Il nome del workflow è obbligatorio' };
    }
    
    // DEBOUNCE CHECK SUBITO ALL'INIZIO
    const debounceId = Date.now();
    
    // Se c'è già un salvataggio in corso (entro 300ms), ignora questa chiamata
    if (saveWorkflow.lastDebounceId && (debounceId - saveWorkflow.lastDebounceId) < 300) {
      console.log('⚠️ Duplicate save call detected within 300ms, ignoring');
      return { success: false, error: 'Salvataggio già in corso' };
    }
    
    saveWorkflow.lastDebounceId = debounceId;
    setIsLoading(true);
    
    try {
      // Salva la vista corrente prima del salvataggio (posizione, zoom, etc.)
      const currentViewport = reactFlowInstance ? reactFlowInstance.getViewport() : null;
      console.log('[WorkflowEditor] Saving current viewport state:', currentViewport);
      
      // Salviamo lo stato del viewport come proprietà statica della funzione
      saveWorkflow.lastViewport = currentViewport;
      
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
        tags: workflowTags,
        // Salva lo stato della vista nel database per recuperarlo tra sessioni diverse
        view_state: currentViewport
      };

      console.log('📤 Sending workflow data to API:', workflowData);
      
      let savedWorkflow;
      
      if (currentWorkflow?.workflow_id) {
        console.log('🔄 Updating existing workflow:', currentWorkflow.workflow_id);
        savedWorkflow = await workflowService.updateWorkflow(currentWorkflow.workflow_id, workflowData);
      } else {
        console.log('✨ Creating new workflow');
        savedWorkflow = await workflowService.createWorkflow(workflowData);
      }

      // Quando impostiamo il currentWorkflow, preserviamo i nodi e le connessioni locali
      // anziché utilizzare quelli restituiti dal server
      const updatedWorkflow = {
        ...savedWorkflow,
        nodes: savedWorkflow.nodes.length > 0 ? savedWorkflow.nodes : nodes.map(node => ({
          node_id: node.id,
          node_type: node.type,
          name: node.data.name,
          description: node.data.description,
          config: node.data.config,
          position: node.position,
          icon: node.data.icon,     // BUGFIX: Preserva l'icona del nodo durante il salvataggio
          color: node.data.color    // BUGFIX: Preserva il colore del nodo durante il salvataggio
        })),
        connections: savedWorkflow.connections.length > 0 ? savedWorkflow.connections : edges.map(edge => ({
          from_node_id: edge.source,
          to_node_id: edge.target,
          from_port: edge.sourceHandle,
          to_port: edge.targetHandle
        }))
      };
      
      setCurrentWorkflow(updatedWorkflow);
      
      if (onSaveCallback) {
        onSaveCallback(updatedWorkflow);
      }
      
      // Ripristina la vista dopo un ritardo più lungo per permettere 
      // al rendering di completarsi dopo l'aggiornamento del state
      if (saveWorkflow.lastViewport && reactFlowInstance) {
        console.log('[WorkflowEditor] Restoring viewport after save:', saveWorkflow.lastViewport);
        
        // Primo tentativo immediato
        reactFlowInstance.setViewport(saveWorkflow.lastViewport);
        
        // Secondo tentativo dopo un ritardo, per essere sicuri
        setTimeout(() => {
          if (reactFlowInstance) {
            console.log('[WorkflowEditor] Delayed viewport restore:', saveWorkflow.lastViewport);
            reactFlowInstance.setViewport(saveWorkflow.lastViewport);
          }
        }, 300);
      }
      
      return { 
        success: true, 
        message: currentWorkflow?.workflow_id ? 'Workflow aggiornato con successo' : 'Workflow creato con successo',
        workflow: updatedWorkflow
      };
    } catch (error) {
      console.error('Error saving workflow:', error);
      return { success: false, error: error.message || 'Errore nel salvataggio del workflow' };
    } finally {
      // Verifica se è stata annullata la richiesta
      if (saveWorkflow.lastDebounceId === debounceId) {
        setIsLoading(false);
      }
    }
  }, [
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
  ]);

  return saveWorkflow;
};
