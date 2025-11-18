import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import workflowService from '../services/workflowService';

const WorkflowManagement = () => {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState([]);
  const [users, setUsers] = useState([]);
  const [recentExecutions, setRecentExecutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignmentType, setAssignmentType] = useState('user'); // 'user' or 'group'
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [groupName, setGroupName] = useState('');
  const [permissions, setPermissions] = useState({
    can_execute: true,
    can_modify: false,
    can_share: false
  });

  // Definisci le funzioni callback PRIMA di useEffect
  const loadUsers = useCallback(async () => {
    try {
      return await workflowService.getUsersForAssignment();
    } catch (error) {
      console.error('Errore caricamento utenti:', error);
      // Fallback to mock users if API fails
      return [
        { id: 'admin', email: 'admin@pramaia.com', role: 'admin' },
        { id: 'user1', email: 'user1@company.com', role: 'user' },
        { id: 'user2', email: 'user2@company.com', role: 'user' },
        { id: 'manager1', email: 'manager1@company.com', role: 'manager' }
      ];
    }
  }, []);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Carica workflow e utenti
      const [workflowsData, usersData] = await Promise.all([
        workflowService.getAllWorkflows(),
        loadUsers() // Funzione mockup per ora
      ]);
      
      setWorkflows(workflowsData);
      setUsers(usersData);
      
      // Prova a caricare le esecuzioni recenti, ma non fallire se l'endpoint non esiste
      try {
        const executionsData = await workflowService.getRecentExecutions(5);
        setRecentExecutions(executionsData);
      } catch (executionError) {
        console.warn('Endpoint esecuzioni recenti non disponibile:', executionError.message);
        setRecentExecutions([]); // Array vuoto se l'endpoint non esiste
      }
      
    } catch (error) {
      setMessage('Errore nel caricamento dei dati: ' + error.message);
    } finally {
      setLoading(false);
    }
  }, [loadUsers]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAssignWorkflow = async () => {
    if (!selectedWorkflow) return;

    try {
      if (assignmentType === 'user') {
        // Assegna a utenti specifici
        for (const userId of selectedUsers) {
          await workflowService.assignWorkflowToUser(
            selectedWorkflow.workflow_id, 
            userId, 
            permissions
          );
        }
        setMessage(`Workflow "${selectedWorkflow.name}" assegnato a ${selectedUsers.length} utenti`);
      } else {
        // Assegna a gruppo
        await workflowService.assignWorkflowToGroup(
          selectedWorkflow.workflow_id,
          groupName,
          permissions
        );
        setMessage(`Workflow "${selectedWorkflow.name}" assegnato al gruppo "${groupName}"`);
      }

      // Ricarica dati e chiudi modal
      await loadData();
      setShowAssignModal(false);
      resetAssignmentForm();
    } catch (error) {
      setMessage('Errore nell\'assegnazione: ' + error.message);
    }
  };

  const resetAssignmentForm = () => {
    setSelectedWorkflow(null);
    setSelectedUsers([]);
    setGroupName('');
    setAssignmentType('user');
    setPermissions({
      can_execute: true,
      can_modify: false,
      can_share: false
    });
  };

  const handleExecuteWorkflow = async (workflowId, workflowName) => {
    try {
      setMessage(`Esecuzione del workflow "${workflowName}" in corso...`);
      await workflowService.executeWorkflow(workflowId, {});
      setMessage(`Workflow "${workflowName}" eseguito con successo!`);
      
      // Ricarica le esecuzioni recenti per mostrare la nuova esecuzione
      try {
        const executionsData = await workflowService.getRecentExecutions(5);
        setRecentExecutions(executionsData);
      } catch (execError) {
        console.error('Errore nel caricamento delle esecuzioni:', execError);
      }
      
      // Auto-clear message after 3 seconds
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      setMessage(`Errore nell'esecuzione del workflow "${workflowName}": ${error.message}`);
      setTimeout(() => setMessage(''), 5000);
    }
  };

  const handleToggleWorkflowStatus = async (workflowId, currentStatus) => {
    try {
      await workflowService.updateWorkflow(workflowId, {
        is_active: !currentStatus
      });
      setMessage(`Workflow ${!currentStatus ? 'attivato' : 'disattivato'} con successo`);
      await loadData();
    } catch (error) {
      setMessage('Errore nel cambio stato: ' + error.message);
    }
  };

  const handleTogglePublicStatus = async (workflowId, currentStatus) => {
    try {
      await workflowService.updateWorkflow(workflowId, {
        is_public: !currentStatus
      });
      setMessage(`Workflow ${!currentStatus ? 'reso pubblico' : 'reso privato'} con successo`);
      await loadData();
    } catch (error) {
      setMessage('Errore nel cambio visibilità: ' + error.message);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4 w-1/3"></div>
          <div className="space-y-3">
            <div className="h-6 bg-gray-200 rounded"></div>
            <div className="h-6 bg-gray-200 rounded"></div>
            <div className="h-6 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-blue-700">🔄 Gestione Workflow</h3>
        <div className="flex space-x-2">
          <button
            onClick={loadData}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
          >
            🔄 Aggiorna
          </button>
          <button
            onClick={() => navigate('/app/workflows/new')}
            className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
          >
            ➕ Nuovo Workflow
          </button>
        </div>
      </div>

      {message && (
        <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-4">
          {message}
          <button 
            onClick={() => setMessage('')}
            className="float-right text-blue-700 hover:text-blue-900"
          >
            ✕
          </button>
        </div>
      )}

      {/* Sezione Esecuzioni Recenti */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h4 className="text-lg font-semibold text-gray-900">📊 Cronologia Esecuzioni</h4>
          <div className="flex space-x-2">
            <button
              onClick={loadData}
              className="text-blue-600 hover:text-blue-800 text-sm px-3 py-1 rounded border border-blue-300 hover:bg-blue-50"
              title="Aggiorna cronologia"
            >
              🔄 Aggiorna
            </button>
          </div>
        </div>

        {recentExecutions.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 text-sm">Nessuna esecuzione recente</p>
          </div>
        ) : (
          <div className="overflow-hidden">
            <div className="align-middle inline-block min-w-full">
              <div className="shadow overflow-hidden border border-gray-200 sm:rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Workflow
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Data e Ora
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Stato
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Durata
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Azioni
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {recentExecutions.map(execution => {
                      // Calcola la durata se l'esecuzione è completata
                      const startTime = new Date(execution.started_at);
                      const endTime = execution.completed_at ? new Date(execution.completed_at) : new Date();
                      const duration = Math.round((endTime - startTime) / 1000); // durata in secondi
                      
                      return (
                        <tr key={execution.execution_id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              {execution.workflow_name}
                            </div>
                            <div className="text-xs text-gray-500">
                              ID: {execution.execution_id}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">
                              {new Date(execution.started_at).toLocaleDateString('it-IT', {
                                day: '2-digit',
                                month: '2-digit',
                                year: '2-digit'
                              })}
                            </div>
                            <div className="text-xs text-gray-500">
                              {new Date(execution.started_at).toLocaleTimeString('it-IT', {
                                hour: '2-digit',
                                minute: '2-digit',
                                second: '2-digit'
                              })}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              execution.status === 'completed' ? 'bg-green-100 text-green-800' :
                              execution.status === 'failed' ? 'bg-red-100 text-red-800' :
                              execution.status === 'running' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {execution.status === 'completed' ? '✓ Completato' :
                               execution.status === 'failed' ? '✗ Fallito' :
                               execution.status === 'running' ? '⟳ In corso' : execution.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {execution.status === 'completed' ? (
                              duration < 60 ? `${duration}s` : `${Math.floor(duration / 60)}m ${duration % 60}s`
                            ) : execution.status === 'running' ? (
                              '⟳ In corso'
                            ) : (
                              '-'
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => navigate(`/app/workflows/${execution.workflow_id}/executions/${execution.execution_id}`)}
                                className="text-blue-600 hover:text-blue-900"
                                title="Visualizza dettagli esecuzione"
                              >
                                📋 Dettagli
                              </button>
                              {execution.status === 'failed' && execution.error && (
                                <button
                                  onClick={() => alert(execution.error)}
                                  className="text-red-600 hover:text-red-900"
                                  title="Visualizza errore"
                                >
                                  ⚠️ Errore
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {workflows.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500 mb-4">Nessun workflow presente nel sistema</p>
          <a
            href="/app/workflow"
            className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg"
          >
            Crea il primo workflow →
          </a>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-0">
                    Workflow
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                    Stato
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                    Visibilità
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                    Assegnazioni
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                    Azioni
                  </th>
                </tr>
              </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {workflows.map((workflow) => (
                <tr key={workflow.workflow_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="max-w-xs">
                      <div className="text-sm font-medium text-gray-900 truncate" title={workflow.name}>
                        {workflow.name}
                      </div>
                      <div className="text-sm text-gray-500 truncate" title={workflow.description || 'Nessuna descrizione'}>
                        {workflow.description || 'Nessuna descrizione'}
                      </div>
                      <div className="text-xs text-gray-400 truncate" title={workflow.workflow_id}>
                        ID: {workflow.workflow_id}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <button
                      onClick={() => handleToggleWorkflowStatus(workflow.workflow_id, workflow.is_active)}
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        workflow.is_active
                          ? 'bg-green-100 text-green-800 hover:bg-green-200'
                          : 'bg-red-100 text-red-800 hover:bg-red-200'
                      }`}
                    >
                      {workflow.is_active ? '✅ Attivo' : '⏸️ Inattivo'}
                    </button>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <button
                      onClick={() => handleTogglePublicStatus(workflow.workflow_id, workflow.is_public)}
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        workflow.is_public
                          ? 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                          : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                      }`}
                    >
                      {workflow.is_public ? '👥 Pubblico' : '🔒 Privato'}
                    </button>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div>
                      <div>👤 Utenti: {workflow.user_assignments?.length || 0}</div>
                      <div>👥 Gruppi: {workflow.assigned_groups?.length || 0}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center space-x-1 flex-wrap gap-1">
                      {workflow.is_active && (
                        <button
                          onClick={() => handleExecuteWorkflow(workflow.workflow_id, workflow.name)}
                          className="text-white bg-blue-600 hover:bg-blue-700 rounded px-2 py-1 text-xs transition-colors"
                          title="Esegui workflow"
                        >
                          ▶️ Esegui
                        </button>
                      )}
                      <button
                        onClick={() => {
                          setSelectedWorkflow(workflow);
                          setShowAssignModal(true);
                        }}
                        className="text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded px-2 py-1 text-xs transition-colors"
                        title="Assegna workflow"
                      >
                        🎯 Assegna
                      </button>
                      <button
                        onClick={() => navigate(`/app/workflows/${workflow.workflow_id}`)}
                        className="text-green-600 hover:text-green-800 hover:bg-green-50 rounded px-2 py-1 text-xs transition-colors"
                        title="Modifica workflow"
                      >
                        ✏️ Modifica
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      )}

      {/* Modal Assegnazione */}
      {showAssignModal && selectedWorkflow && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                🎯 Assegna Workflow: {selectedWorkflow.name}
              </h3>

              {/* Tipo di assegnazione */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tipo di assegnazione:
                </label>
                <div className="flex space-x-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="assignmentType"
                      value="user"
                      checked={assignmentType === 'user'}
                      onChange={(e) => setAssignmentType(e.target.value)}
                      className="mr-2"
                    />
                    👤 Utenti specifici
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="assignmentType"
                      value="group"
                      checked={assignmentType === 'group'}
                      onChange={(e) => setAssignmentType(e.target.value)}
                      className="mr-2"
                    />
                    👥 Gruppo
                  </label>
                </div>
              </div>

              {/* Selezione utenti o gruppo */}
              {assignmentType === 'user' ? (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Seleziona utenti:
                  </label>
                  <div className="max-h-32 overflow-y-auto border border-gray-300 rounded p-2">
                    {users.map(user => (
                      <label key={user.id} className="flex items-center py-1">
                        <input
                          type="checkbox"
                          checked={selectedUsers.includes(user.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedUsers([...selectedUsers, user.id]);
                            } else {
                              setSelectedUsers(selectedUsers.filter(id => id !== user.id));
                            }
                          }}
                          className="mr-2"
                        />
                        <span className="text-sm">
                          {user.email} ({user.role})
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nome gruppo:
                  </label>
                  <input
                    type="text"
                    value={groupName}
                    onChange={(e) => setGroupName(e.target.value)}
                    placeholder="es: sales, support, managers"
                    className="w-full border border-gray-300 rounded px-3 py-2"
                  />
                </div>
              )}

              {/* Permessi */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Permessi:
                </label>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={permissions.can_execute}
                      onChange={(e) => setPermissions({
                        ...permissions,
                        can_execute: e.target.checked
                      })}
                      className="mr-2"
                    />
                    <span className="text-sm">▶️ Può eseguire il workflow</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={permissions.can_modify}
                      onChange={(e) => setPermissions({
                        ...permissions,
                        can_modify: e.target.checked
                      })}
                      className="mr-2"
                    />
                    <span className="text-sm">✏️ Può modificare il workflow</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={permissions.can_share}
                      onChange={(e) => setPermissions({
                        ...permissions,
                        can_share: e.target.checked
                      })}
                      className="mr-2"
                    />
                    <span className="text-sm">🔗 Può condividere il workflow</span>
                  </label>
                </div>
              </div>

              {/* Pulsanti */}
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowAssignModal(false);
                    resetAssignmentForm();
                  }}
                  className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded"
                >
                  Annulla
                </button>
                <button
                  onClick={handleAssignWorkflow}
                  disabled={
                    assignmentType === 'user' ? selectedUsers.length === 0 : !groupName.trim()
                  }
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded disabled:bg-gray-300"
                >
                  🎯 Assegna Workflow
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowManagement;
