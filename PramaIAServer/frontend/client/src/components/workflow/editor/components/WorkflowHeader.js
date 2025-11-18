import React from 'react';

/**
 * Componente header/toolbar del WorkflowEditor
 */
const WorkflowHeader = ({
  currentWorkflow,
  workflowName,
  workflowDescription,
  workflowCategory,
  isLoading,
  reactFlowInstance,
  onWorkflowNameChange,
  onWorkflowDescriptionChange,
  onWorkflowCategoryChange,
  onSave,
  onLoad,
  onClose,
  onShowTagEditor,
  onNavigateToList
}) => {
  return (
    <div className="bg-white border-b border-gray-200 p-4">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {currentWorkflow ? `Modifica: ${currentWorkflow.name}` : 'Nuovo Workflow'}
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            {currentWorkflow 
              ? 'Modifica il workflow esistente' 
              : 'Crea un nuovo workflow trascinando i nodi dalla palette'
            }
          </p>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={onLoad}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
          >
            Carica
          </button>
          
          <button
            onClick={() => {
              if (reactFlowInstance) {
                reactFlowInstance.fitView({ padding: 0.1 });
              }
            }}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
            title="Centra la vista sui nodi"
          >
            📍 Centra
          </button>
          
          {onShowTagEditor && (
            <button
              onClick={onShowTagEditor}
              className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 transition-colors"
            >
              Tags
            </button>
          )}
          
          <button
            onClick={onSave}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 transition-colors"
          >
            {isLoading ? 'Salvando...' : 'Salva'}
          </button>
          
          {onNavigateToList && (
            <button
              onClick={onNavigateToList}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
              title="Torna all'elenco dei workflow"
            >
              Torna all'elenco
            </button>
          )}
          
          {onClose && (
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 transition-colors"
            >
              Chiudi
            </button>
          )}
        </div>
      </div>
      
      {/* Campi nome, descrizione e categoria */}
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Nome Workflow
          </label>
          <input
            type="text"
            value={workflowName}
            onChange={(e) => onWorkflowNameChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            onChange={(e) => onWorkflowDescriptionChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Descrizione opzionale"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Categoria
          </label>
          <select
            value={workflowCategory}
            onChange={(e) => onWorkflowCategoryChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="General">General</option>
            <option value="PDF">PDF</option>
            <option value="AI">AI</option>
            <option value="Data Processing">Data Processing</option>
            <option value="Integration">Integration</option>
            <option value="Automation">Automation</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default WorkflowHeader;
