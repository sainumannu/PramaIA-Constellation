import React, { useState, useEffect } from 'react';
import InputNodeSelector from '../components/InputNodeSelector';
import workflowService from '../services/workflowService';

const TriggerTestPage = () => {
  const [workflows, setWorkflows] = useState([]);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState('');
  const [selectedNodeId, setSelectedNodeId] = useState('');
  const [eventType, setEventType] = useState('pdf_upload');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      const workflowsData = await workflowService.getAllWorkflows();
      setWorkflows(workflowsData);
    } catch (error) {
      console.error('Errore caricamento workflow:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleWorkflowChange = (e) => {
    const workflowId = e.target.value;
    setSelectedWorkflowId(workflowId);
    setSelectedNodeId(''); // Reset del nodo selezionato
  };

  const handleNodeSelect = (nodeId) => {
    setSelectedNodeId(nodeId);
    console.log('Nodo selezionato:', nodeId);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Configurazione trigger:', {
      workflowId: selectedWorkflowId,
      targetNodeId: selectedNodeId,
      eventType: eventType
    });
    alert(`Trigger configurato:\nWorkflow: ${selectedWorkflowId}\nNodo: ${selectedNodeId}\nEvento: ${eventType}`);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        🧪 Test Sistema di Trigger con Selezione Nodi
      </h1>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Selezione Workflow */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Workflow
          </label>
          <select
            value={selectedWorkflowId}
            onChange={handleWorkflowChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          >
            <option value="">Seleziona un workflow...</option>
            {workflows.map(workflow => (
              <option key={workflow.workflow_id} value={workflow.workflow_id}>
                {workflow.name} ({workflow.workflow_id})
              </option>
            ))}
          </select>
        </div>

        {/* Tipo di Evento */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Tipo di Evento
          </label>
          <select
            value={eventType}
            onChange={(e) => setEventType(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="pdf_upload">PDF Upload</option>
            <option value="query_request">Query Request</option>
            <option value="file_created">File Created</option>
            <option value="text_input">Text Input</option>
            <option value="image_upload">Image Upload</option>
          </select>
        </div>

        {/* Selezione Nodo di Input - Nuovo Componente */}
        <InputNodeSelector
          workflowId={selectedWorkflowId}
          selectedNodeId={selectedNodeId}
          onNodeSelect={handleNodeSelect}
          triggerEventType={eventType}
          className="border border-gray-200 p-4 rounded-lg bg-gray-50"
        />

        {/* Risultato */}
        {selectedWorkflowId && selectedNodeId && (
          <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
            <h3 className="font-medium text-green-800 mb-2">✅ Configurazione Attuale</h3>
            <div className="text-sm text-green-700 space-y-1">
              <div><strong>Workflow:</strong> {selectedWorkflowId}</div>
              <div><strong>Nodo Target:</strong> {selectedNodeId}</div>
              <div><strong>Evento:</strong> {eventType}</div>
            </div>
          </div>
        )}

        {/* Pulsanti */}
        <div className="flex gap-4">
          <button
            type="submit"
            disabled={!selectedWorkflowId || !selectedNodeId}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Crea Trigger di Test
          </button>
          
          <button
            type="button"
            onClick={() => {
              setSelectedWorkflowId('');
              setSelectedNodeId('');
              setEventType('pdf_upload');
            }}
            className="px-6 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Reset
          </button>
        </div>
      </form>

      {loading && (
        <div className="mt-4 text-center text-gray-600">
          Caricamento workflow...
        </div>
      )}
    </div>
  );
};

export default TriggerTestPage;
