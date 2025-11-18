import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import WorkflowEditor from '../components/workflow/editor/WorkflowEditor.js';
import workflowService from '../services/workflowService.js';
import toast, { Toaster } from 'react-hot-toast';

const WorkflowPage = () => {
  const [workflows, setWorkflows] = useState([]);
  const [currentWorkflow, setCurrentWorkflow] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false); // Flag per prevenire doppi submit
  const { id: workflowId } = useParams();
  
  // Ottieni il token dal localStorage
  const token = localStorage.getItem('token');

  // Carica workflow specifico
  const handleLoadWorkflow = useCallback(async (workflowId) => {
    try {
      console.log('=== WORKFLOWPAGE LOAD DEBUG ===');
      console.log('Loading workflow ID:', workflowId);
      const workflow = await workflowService.getWorkflow(workflowId);
      console.log('Loaded workflow from API:', workflow);
      setCurrentWorkflow(workflow);
      console.log('Set currentWorkflow in WorkflowPage');
      return workflow;
    } catch (error) {
      console.error('Errore caricamento workflow:', error);
      toast.error(error.message || 'Errore nel caricamento del workflow');
      throw error;
    }
  }, []);

  // Check for workflow ID in URL parameters
  useEffect(() => {
    if (workflowId && workflowId !== 'new') {
      console.log('[WorkflowPage] Loading workflow from route params:', workflowId);
      handleLoadWorkflow(workflowId);
    }
  }, [workflowId, handleLoadWorkflow]);

  // Carica lista workflow
  const loadWorkflows = async () => {
    try {
      setLoading(true);
      const workflows = await workflowService.getAllWorkflows();
      setWorkflows(workflows);
    } catch (error) {
      console.error('Errore caricamento workflow:', error);
      toast.error(error.message || 'Errore nel caricamento dei workflow');
    } finally {
      setLoading(false);
    }
  };

  // Salva workflow
  const handleSaveWorkflow = async (workflowData, options = {}) => {
    // DEBUGGING: Traccia chi sta chiamando questa funzione
    console.log('🔴 handleSaveWorkflow CALLED - Stack trace:');
    console.trace();
    
    // Previeni doppi submit
    if (isSaving) {
      console.log('⚠️ Save already in progress, ignoring duplicate call');
      return;
    }
    
    try {
      setIsSaving(true);
      console.log('=== WORKFLOWPAGE SAVE DEBUG ===');
      console.log('workflowData:', workflowData);
      console.log('options:', options);
      console.log('currentWorkflow before save:', currentWorkflow);
      
      let response;
      if (currentWorkflow) {
        // Update existing
        response = await workflowService.updateWorkflow(
          currentWorkflow.workflow_id,
          workflowData
        );
        console.log('Update response:', response);
      } else {
        // Create new
        response = await workflowService.createWorkflow(workflowData);
        console.log('Create response:', response);
      }
      
      // Always update currentWorkflow with the latest data from the server
      console.log('Setting currentWorkflow to:', response);
      setCurrentWorkflow(response);
      
      // Note: Non ricarichiamo la lista qui per evitare duplicati
      // La lista verrà ricaricata quando l'utente torna alla WorkflowListPage
      
      return response;
    } catch (error) {
      console.error('Errore salvataggio workflow:', error);
      toast.error(error.message || 'Errore nel salvataggio del workflow');
      throw error;
    } finally {
      setIsSaving(false);
    }
  };

  // Esegui workflow
  const handleExecuteWorkflow = async (executionData) => {
    if (!currentWorkflow) {
      throw new Error('Salva il workflow prima di eseguirlo');
    }

    try {
      const result = await workflowService.executeWorkflow(
        currentWorkflow.workflow_id,
        executionData
      );
      toast.success('Workflow eseguito con successo!');
      return result;
    } catch (error) {
      console.error('Errore esecuzione workflow:', error);
      toast.error(error.message || 'Errore nell\'esecuzione del workflow');
      throw error;
    }
  };

  useEffect(() => {
    if (token) {
      loadWorkflows();
    }
  }, [token]);

  if (!token) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Accesso Richiesto</h2>
          <p className="text-gray-600">Effettua il login per accedere all'editor workflow.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Workflow Editor</h1>
            <p className="text-gray-600">Crea e gestisci i tuoi workflow automatizzati</p>
          </div>
          
          {/* Workflow Selector */}
          <div className="flex items-center space-x-4">
            <select
              value={currentWorkflow?.workflow_id || ''}
              onChange={(e) => {
                if (e.target.value) {
                  handleLoadWorkflow(e.target.value);
                } else {
                  setCurrentWorkflow(null);
                }
              }}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Nuovo Workflow</option>
              {workflows.map(wf => (
                <option key={wf.workflow_id} value={wf.workflow_id}>
                  {wf.name} ({wf.nodes_count} nodi)
                </option>
              ))}
            </select>
            
            <button
              onClick={loadWorkflows}
              disabled={loading}
              className="px-3 py-2 text-gray-600 hover:text-gray-900 transition-colors"
              title="Aggiorna lista"
            >
              {loading ? '⟳' : '↻'}
            </button>
          </div>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1">
        <WorkflowEditor
          workflowId={workflowId}
          workflowData={currentWorkflow}
          onSave={handleSaveWorkflow}
          onLoad={handleLoadWorkflow}
          onExecute={handleExecuteWorkflow}
        />
      </div>
      <Toaster position="top-right" />
    </div>
  );
};

export default WorkflowPage;
