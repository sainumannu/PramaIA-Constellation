import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import UsageStats from "./UsageStats"; // Importa il nuovo componente
import PDKPluginList from "./PDKPluginList";
import NotebookSourcesManager from './NotebookSourcesManager';
import WorkflowManagement from './WorkflowManagement'; // Nuovo import per gestione workflow
import OllamaManager from './OllamaManager'; // Import per gestione Ollama
import SystemSettings from './SystemSettings'; // Import per impostazioni di sistema
import PdfEventsSettings from './PdfEventsSettings'; // Import per impostazioni eventi PDF
import config from '../config';

function DashboardAdmin({ onBack }) {
  // State for existing functionality (User Data Viewer)
  const [selectedUserIdForView, setSelectedUserIdForView] = useState('admin'); // Renamed for clarity
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [tokenUsage, setTokenUsage] = useState(0);
  const [logEntries, setLogEntries] = useState([]);
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');

  // New state for User & Domain Management
  const [adminTab, setAdminTab] = useState('userDataViewer'); // 'userDataViewer', 'notebookManagement', etc.
  const [maxInteractions, setMaxInteractions] = useState(() => {
    // Carica da localStorage o default a 100
    return Number(localStorage.getItem('maxInteractions')) || 100;
  });

  // State for Notebook Management
  const [allNotebooks, setAllNotebooks] = useState([]);
  const [notebookLoading, setNotebookLoading] = useState(false);
  const [notebookMessage, setNotebookMessage] = useState('');
  const [showSourcesManager, setShowSourcesManager] = useState(false);
  const [selectedNotebookId, setSelectedNotebookId] = useState(null);
  

  // --- Fetch Functions for User Data Viewer (tied to selectedUserIdForView) ---
  const fetchFilesForUser = async (userIdToFetch) => {
    try {
      const res = await axios.get(`${config.BACKEND_URL}/documents/?user_id=${userIdToFetch}`);
      setFiles(res.data.files);
    } catch (err) {
      console.error('Errore nel recupero documenti:', err);
    }
  };
  const fetchTokenUsageForUser = async (userIdToFetch) => {
    try {
      const res = await axios.get(`${config.BACKEND_URL}/tokens/summary?user_id=${userIdToFetch}`);
      setTokenUsage(res.data.total_tokens);
    } catch (err) {
      console.error('Errore nel recupero token:', err);
    }
  };

  const fetchLogEntriesForUser = useCallback(async (userIdToFetch) => {
    try {
      let url = `${config.BACKEND_URL}/tokens/log?user_id=${userIdToFetch}`;
      if (fromDate) url += `&from_date=${fromDate}`;
      if (toDate) url += `&to_date=${toDate}`;
      const res = await axios.get(url);
      setLogEntries(res.data);
    } catch (err) {
      console.error('Errore nel recupero storico:', err);
    }
  }, [fromDate, toDate]);

  useEffect(() => {
    // Fetch data for the "User Data Viewer" tab
    if (adminTab === 'userDataViewer' && selectedUserIdForView) {
      fetchFilesForUser(selectedUserIdForView);
      fetchTokenUsageForUser(selectedUserIdForView);
      fetchLogEntriesForUser(selectedUserIdForView);
    }
  }, [selectedUserIdForView, adminTab, fromDate, toDate, fetchLogEntriesForUser]);

  // --- Handlers for User Data Viewer ---
  const handleDeleteFile = async (filename) => {
    setLoading(true);
    setMessage(`Eliminazione di "${filename}" (per utente ${selectedUserIdForView}) in corso...`);
    try {
      // Ensure your backend handles authorization for this admin action
      await axios.delete(`${config.BACKEND_URL}/documents/${encodeURIComponent(filename)}?user_id=${selectedUserIdForView}`);
      fetchFilesForUser(selectedUserIdForView); // Re-fetch files for the current user
      setMessage(`File "${filename}" eliminato.`);
    } catch (err) {
      console.error('Errore durante eliminazione:', err);
      setMessage('Errore durante l\'eliminazione.');
    } finally {
      setLoading(false);
      setTimeout(() => setMessage(''), 3000);
    }
  };

  const handleFilterLogs = () => {
    if (selectedUserIdForView) {
      fetchLogEntriesForUser(selectedUserIdForView);
    }
  };

  const filteredManagedUsers = []; // Rimosso, ora gestito in UserManagementPage

  // --- Notebook Management Functions ---
  const fetchAllNotebooks = async () => {
    setNotebookLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${config.BACKEND_URL}/sessions/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      // Admin riceve view_type: "admin_enhanced" con info sui proprietari
      const data = res.data;
      if (data.view_type === "admin_enhanced" && data.sessions) {
        const notebooksList = Object.entries(data.sessions).map(([sessionId, sessionData]) => ({
          sessionId,
          title: sessionData.title || 'Notebook senza titolo',
          owner: sessionData.owner,
          createdAt: sessionData.created_at,
          entryCount: sessionData.entry_count
        }));
        setAllNotebooks(notebooksList);
      } else {
        // Fallback per formato normale
        const sessions = data.sessions || data;
        const notebooksList = Object.entries(sessions).map(([sessionId, entries]) => {
          const first = entries[0] || {};
          return {
            sessionId,
            title: first.title || 'Notebook senza titolo',
            owner: first.user_id || 'Sconosciuto',
            createdAt: first.timestamp,
            entryCount: entries.length
          };
        }).filter(nb => nb.sessionId !== 'unknown');
        setAllNotebooks(notebooksList);
      }
      
      setNotebookMessage('');
    } catch (error) {
      console.error('Errore nel caricamento notebook:', error);
      setNotebookMessage('Errore nel caricamento dei notebook');
      setAllNotebooks([]);
    } finally {
      setNotebookLoading(false);
    }
  };

  const handleDeleteNotebookAdmin = async (sessionId, owner) => {
    if (!window.confirm(`Sei sicuro di voler eliminare il notebook "${sessionId}" di ${owner}?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${config.BACKEND_URL}/sessions/admin/users/${owner}/sessions/${sessionId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      setNotebookMessage(`Notebook "${sessionId}" eliminato con successo`);
      fetchAllNotebooks(); // Ricarica la lista
      setTimeout(() => setNotebookMessage(''), 3000);
    } catch (error) {
      console.error('Errore nell\'eliminazione:', error);
      const errorMsg = error.response?.data?.detail || 'Errore nell\'eliminazione del notebook';
      setNotebookMessage(errorMsg);
      setTimeout(() => setNotebookMessage(''), 3000);
    }
  };

  const handleManageNotebookSources = (sessionId) => {
    setSelectedNotebookId(sessionId);
    setShowSourcesManager(true);
  };

  // Fetch notebooks when switching to notebook management tab
  useEffect(() => {
    if (adminTab === 'notebookManagement') {
      fetchAllNotebooks();
    }
  }, [adminTab]);

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-blue-700">Dashboard Admin</h2>
        {/* Pulsante torna alla chat rimosso */}
      </div>

      {/* Tabs */}

      <div className="mb-4 border-b border-gray-300">
        <nav className="flex space-x-4">
          <button
            onClick={() => setAdminTab('pdkPlugins')}
            className={`py-2 px-4 font-medium ${adminTab === 'pdkPlugins' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-800'}`}
          >
            🧩 Plugin PDK
          </button>
          <button
            onClick={() => setAdminTab('userDataViewer')}
            className={`py-2 px-4 font-medium ${adminTab === 'userDataViewer' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-800'}`}
          >
            Visualizzatore Dati Utente
          </button>
          <button
            onClick={() => setAdminTab('notebookManagement')}
            className={`py-2 px-4 font-medium ${adminTab === 'notebookManagement' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-800'}`}
          >
            Gestione Notebook
          </button>
          <button
            onClick={() => setAdminTab('workflowManagement')}
            className={`py-2 px-4 font-medium ${adminTab === 'workflowManagement' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-800'}`}
          >
            🔄 Gestione Workflow
          </button>
          <button
            onClick={() => setAdminTab('llmManagement')}
            className={`py-2 px-4 font-medium ${adminTab === 'llmManagement' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-800'}`}
          >
            Gestione Modelli LLM
          </button>
          <button
            onClick={() => setAdminTab('usage')}
            className={`py-2 px-4 font-medium ${adminTab === 'usage' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-800'}`}
          >
            Utilizzo
          </button>
          <button
            onClick={() => setAdminTab('settings')}
            className={`py-2 px-4 font-medium ${adminTab === 'settings' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-800'}`}
          >
            Impostazioni
          </button>
        </nav>
      </div>

      {adminTab === 'pdkPlugins' && (
        <PDKPluginList />
      )}

      {adminTab === 'userDataViewer' && (
        <div className="flex-1 overflow-y-auto">
          <div className="mb-4">
            <label className="block mb-1">Seleziona Utente per visualizzare i dati:</label>
            <select
              value={selectedUserIdForView}
              onChange={(e) => setSelectedUserIdForView(e.target.value)}
              className="p-2 border rounded"
            >
              <option value="admin">admin</option>
              <option value="utente1">utente1</option>
              {/* TODO: Populate this list dynamically, e.g., from managedUsers if appropriate */}
            </select>
          </div>

          <p className="text-sm text-gray-700 mb-2">🔢 Token utilizzati (per {selectedUserIdForView}): <strong>{tokenUsage}</strong></p>
          {message && <p className="text-sm text-gray-700 mb-2">{message}</p>}

          <div className="mb-6">
            <h3 className="font-semibold mb-1">📋 Storico richieste (per {selectedUserIdForView})</h3>
            <div className="flex items-center gap-2 mb-2">
              <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} className="p-1 border rounded" />
              <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} className="p-1 border rounded" />
              <button onClick={handleFilterLogs} className="bg-blue-600 text-white px-3 py-1 rounded">Filtra</button>
            </div>
            <div className="h-40 overflow-y-auto bg-white p-2 rounded shadow">
              {logEntries.length === 0 ? (
                <p className="text-sm text-gray-500">Nessuna richiesta registrata per {selectedUserIdForView}.</p>
              ) : (
                <ul className="text-sm space-y-1">
                  {logEntries.map((entry, idx) => (
                    <li key={idx}>
                      <span className="font-mono text-gray-600">{entry.timestamp}</span> –
                      <span className="ml-2">{entry.prompt}</span> –
                      <span className="ml-2 text-blue-700">{entry.tokens} tokens</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div> {/* Removed flex-1 from here, parent div has it */}
            <h3 className="font-semibold mb-2">📂 Documenti caricati (da {selectedUserIdForView}):</h3>
            {loading && <p>Caricamento documenti...</p>}
            {files.length === 0 && !loading ? (
              <p className="text-sm text-gray-600">Nessun documento disponibile per {selectedUserIdForView}.</p>
            ) : (
              <ul className="space-y-2">
                {files.map((file, idx) => (
                  <li key={idx} className="bg-white p-3 rounded shadow flex justify-between items-center">
                    <div>
                      <p className="text-sm font-mono">📄 {file.filename}</p>
                      <p className="text-xs text-gray-500">👤 {file.owner}</p>
                    </div>
                    <button
                      className="bg-red-600 text-white px-3 py-1 rounded disabled:opacity-50"
                      onClick={() => handleDeleteFile(file.filename)}
                      disabled={loading}
                    >
                      Elimina
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {adminTab === 'llmManagement' && (
        <div>
          <h3 className="text-lg font-semibold mb-3 text-blue-600">Gestione Modelli LLM</h3>
          
          <div className="mb-4 p-3 bg-blue-100 rounded text-blue-900">
            <p><strong>🦙 Ollama Manager</strong></p>
            <p className="text-sm mt-1">Gestisci modelli LLM locali con Ollama per massima privacy e controllo.</p>
          </div>
          
          <OllamaManager />
          
          <div className="mt-6 p-3 bg-yellow-100 rounded text-yellow-900 font-semibold">
            OpenAI non permette più di recuperare il credito via API.<br />
            Controlla il credito direttamente dalla <a href="https://platform.openai.com/usage" target="_blank" rel="noopener noreferrer" className="underline text-blue-700">dashboard OpenAI</a>.
          </div>
        </div>
      )}

      {adminTab === 'notebookManagement' && (
        <div>
          <h3 className="text-lg font-semibold mb-3 text-blue-600">Gestione Notebook (Tutti gli Utenti)</h3>
          
          {notebookMessage && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md text-sm">
              {notebookMessage}
            </div>
          )}

          <div className="mb-4">
            <button
              onClick={fetchAllNotebooks}
              disabled={notebookLoading}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md disabled:opacity-50"
            >
              {notebookLoading ? 'Caricamento...' : 'Ricarica Notebook'}
            </button>
          </div>

          {notebookLoading ? (
            <div className="text-center py-8">Caricamento notebook...</div>
          ) : (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              {allNotebooks.length === 0 ? (
                <div className="p-6 text-center text-gray-500">
                  Nessun notebook trovato
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          ID Sessione
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Titolo
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Proprietario
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Creato
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Messaggi
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Azioni
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {allNotebooks.map((notebook) => (
                        <tr key={notebook.sessionId}>
                          <td className="px-4 py-2 whitespace-nowrap text-sm font-mono text-gray-700">
                            {notebook.sessionId}
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-700">
                            {notebook.title}
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-700">
                            {notebook.owner}
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-700">
                            {notebook.createdAt ? new Date(notebook.createdAt).toLocaleString() : 'N/D'}
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-700">
                            {notebook.entryCount || 0}
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap text-sm">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => handleManageNotebookSources(notebook.sessionId)}
                                className="bg-blue-500 hover:bg-blue-600 text-white px-2 py-1 rounded text-xs"
                                title="Gestisci fonti"
                              >
                                📂 Fonti
                              </button>
                              <button
                                onClick={() => handleDeleteNotebookAdmin(notebook.sessionId, notebook.owner)}
                                className="bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded text-xs"
                                title="Elimina notebook"
                              >
                                🗑️ Elimina
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab Workflow Management */}
      {adminTab === 'workflowManagement' && <WorkflowManagement />}

      {/* Tab Usage - Statistiche di utilizzo */}
      {adminTab === 'usage' && <UsageStats />}

      {/* Tab Settings - Impostazioni Generali */}
      {adminTab === 'settings' && (
        <div className="space-y-6">
          {/* Impostazioni di Interazione */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-semibold mb-4">⚙️ Impostazioni Chat</h3>
            
            <div className="space-y-6">
              {/* Impostazione Max Interactions */}
              <div className="border-b pb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Numero massimo di messaggi da considerare per il contesto
                </label>
                <div className="flex items-center space-x-3">
                  <input
                    type="number"
                    value={maxInteractions}
                    onChange={(e) => setMaxInteractions(Number(e.target.value))}
                    min="1"
                    max="1000"
                    className="border border-gray-300 rounded px-3 py-2 w-24"
                  />
                  <button
                    onClick={() => {
                      localStorage.setItem('maxInteractions', maxInteractions);
                      setMessage('Impostazioni salvate correttamente!');
                      setTimeout(() => setMessage(''), 3000);
                    }}
                    className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
                  >
                    Salva
                  </button>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  Controlla quanti messaggi precedenti vengono considerati quando l'AI risponde. 
                  Valori più alti = più contesto ma più costi di token.
                </p>
              </div>

              {/* Altre impostazioni chat possono essere aggiunte qui */}
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Informazioni Sistema</h4>
                <div className="bg-gray-50 rounded p-3 text-sm">
                  <p><strong>Max Interactions corrente:</strong> {maxInteractions}</p>
                  <p><strong>Storage utilizzato:</strong> localStorage</p>
                  <p><strong>Versione:</strong> PramaIA 2.0</p>
                </div>
              </div>
            </div>

            {message && (
              <div className="mt-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
                {message}
              </div>
            )}
          </div>
          
          {/* Impostazioni di Sistema */}
          <SystemSettings />
          
          {/* Impostazioni Eventi PDF */}
          <PdfEventsSettings />
        </div>
      )}

      {/* Notebook Sources Manager Modal */}
      {showSourcesManager && (
        <NotebookSourcesManager
          sessionId={selectedNotebookId}
          isOpen={showSourcesManager}
          onClose={() => {
            setShowSourcesManager(false);
            setSelectedNotebookId(null);
          }}
          isAdmin={true}
        />
      )}
    </div>
  );
}

export default DashboardAdmin;
