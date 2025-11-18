import React, { useState, useEffect } from 'react';
import workflowService from '../services/workflowService';

const WorkflowSelector = ({ onWorkflowSelect, currentWorkflow }) => {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    const fetchWorkflows = async () => {
      try {
        setLoading(true);
        const userWorkflows = await workflowService.getAllWorkflows();
        const activeWorkflows = userWorkflows.filter(w => w.is_active);
        setWorkflows(activeWorkflows);
      } catch (error) {
        console.error('Errore caricamento workflow:', error);
        setWorkflows([]);
      } finally {
        setLoading(false);
      }
    };

    fetchWorkflows();
  }, []);

  const handleWorkflowSelect = (workflow) => {
    onWorkflowSelect(workflow);
    setShowDropdown(false);
  };

  const handleClearWorkflow = () => {
    onWorkflowSelect(null);
    setShowDropdown(false);
  };

  if (loading) {
    return (
      <div className="mb-4 p-3 bg-gray-50 rounded-lg">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3"></div>
        </div>
      </div>
    );
  }

  if (workflows.length === 0) {
    return (
      <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="flex items-center">
          <span className="text-yellow-600 text-sm">
            ⚠️ Nessun workflow disponibile
          </span>
          <a 
            href="/app/workflows" 
            className="ml-2 text-blue-600 hover:text-blue-800 text-sm underline"
          >
            Crea workflow →
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-4 relative">
      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-700">🔄 Workflow:</span>
          {currentWorkflow ? (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-blue-600 bg-blue-100 px-2 py-1 rounded">
                {currentWorkflow.name}
              </span>
              <button
                onClick={handleClearWorkflow}
                className="text-gray-400 hover:text-red-500 text-xs"
                title="Rimuovi workflow"
              >
                ✕
              </button>
            </div>
          ) : (
            <span className="text-sm text-gray-500">Nessun workflow selezionato</span>
          )}
        </div>
        
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="text-blue-600 hover:text-blue-800 text-sm px-3 py-1 rounded border border-blue-300 hover:bg-blue-50"
        >
          {currentWorkflow ? 'Cambia' : 'Seleziona'} ▼
        </button>
      </div>

      {/* Dropdown Menu */}
      {showDropdown && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto">
          <div className="p-2">
            <div className="text-xs text-gray-500 uppercase tracking-wide mb-2 px-2">
              Workflow Disponibili ({workflows.length})
            </div>
            
            {/* Opzione "Nessun workflow" */}
            <button
              onClick={handleClearWorkflow}
              className="w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm"
            >
              <div className="flex items-center">
                <span className="text-gray-600">💬 Chat normale (senza workflow)</span>
              </div>
            </button>

            <div className="border-t border-gray-100 my-1"></div>

            {/* Lista workflow */}
            {workflows.map(workflow => (
              <button
                key={workflow.workflow_id}
                onClick={() => handleWorkflowSelect(workflow)}
                className={`w-full text-left px-3 py-2 rounded hover:bg-blue-50 text-sm ${
                  currentWorkflow?.workflow_id === workflow.workflow_id 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'text-gray-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{workflow.name}</div>
                    <div className="text-xs text-gray-500 truncate">
                      {workflow.description || 'Nessuna descrizione'}
                    </div>
                  </div>
                  <div className="flex items-center space-x-1">
                    {workflow.is_public && (
                      <span className="text-xs text-green-600">👥</span>
                    )}
                    <span className="text-xs text-blue-600">🔄</span>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {/* Footer */}
          <div className="border-t border-gray-100 p-2">
            <a 
              href="/app/workflows"
              className="block text-center text-blue-600 hover:text-blue-800 text-xs py-1"
            >
              🔧 Gestisci Workflow
            </a>
          </div>
        </div>
      )}

      {/* Click outside to close */}
      {showDropdown && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowDropdown(false)}
        />
      )}
    </div>
  );
};

export default WorkflowSelector;
