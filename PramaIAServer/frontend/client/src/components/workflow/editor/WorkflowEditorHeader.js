import React from 'react';
import { WORKFLOW_CATEGORIES } from '../../../config/appConfig';

/**
 * Componente per l'intestazione dell'editor di workflow
 * 
 * @param {Object} props - Proprietà del componente
 * @returns {JSX.Element} - Componente React
 */
const WorkflowEditorHeader = ({
  currentWorkflow,
  workflowName,
  workflowDescription,
  workflowCategory,
  isLoading,
  setWorkflowName,
  setWorkflowDescription,
  setWorkflowCategory,
  setShowSelectModal,
  setShowTagEditor,
  saveWorkflow,
  onClose,
  onNavigateToList,
  reactFlowInstance
}) => {
  return (
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
            onClick={() => {
              if (reactFlowInstance) {
                reactFlowInstance.fitView({ padding: 0.1 });
              }
            }}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            title="Centra la vista sui nodi"
          >
            📍 Centra
          </button>
          <button
            onClick={saveWorkflow}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {isLoading ? 'Salvando...' : 'Salva'}
          </button>
          <button
            onClick={onNavigateToList}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            title="Torna all'elenco dei workflow"
          >
            Torna all'elenco
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
      <div className="mt-4 grid grid-cols-3 gap-4">
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
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Categoria
          </label>
          <div className="relative">
            <select
              value={workflowCategory}
              onChange={(e) => {
                if (e.target.value === "custom") {
                  // Mostra input per categoria personalizzata
                  const customCategory = prompt("Inserisci il nome della nuova categoria:");
                  if (customCategory && customCategory.trim()) {
                    setWorkflowCategory(customCategory.trim());
                  }
                } else {
                  setWorkflowCategory(e.target.value);
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              {WORKFLOW_CATEGORIES.map(category => (
                <option key={category.value} value={category.value}>
                  {category.label}
                </option>
              ))}
              <option value="custom">Personalizzata...</option>
            </select>
            {workflowCategory && !WORKFLOW_CATEGORIES.map(c => c.value).includes(workflowCategory) && (
              <div className="mt-2 text-sm text-blue-600">
                Categoria personalizzata: {workflowCategory}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkflowEditorHeader;
