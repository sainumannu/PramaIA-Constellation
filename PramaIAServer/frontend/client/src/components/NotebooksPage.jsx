import React, { useEffect, useState } from 'react';
import axios from 'axios';
import NewNotebookDialog from './NewNotebookDialog';
import NotebookSourcesManager from './NotebookSourcesManager';
import DocumentsManager from './DocumentsManager';
import config from '../config';

function NotebooksPage({ onOpenNotebook }) {
  const [notebooks, setNotebooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showSourcesManager, setShowSourcesManager] = useState(false);
  const [showDocumentsManager, setShowDocumentsManager] = useState(false);
  const [selectedNotebookId, setSelectedNotebookId] = useState(null);

  const loadNotebooks = () => {
    console.log("=== CARICAMENTO NOTEBOOKS ===");
    const token = localStorage.getItem('token');
    console.log("Token per caricamento:", token ? "Presente" : "Assente");
    
    axios.get(`${config.BACKEND_URL}/sessions/history?_t=${Date.now()}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
      .then(res => {
        console.log("Risposta sessions/history (RAW):", res);
        console.log("Risposta sessions/history (DATA):", res.data);
        console.log("Tipo di risposta:", typeof res.data);
        console.log("Chiavi della risposta:", Object.keys(res.data || {}));
        
        const sessions = res.data || {};
        const entries = Object.entries(sessions);
        console.log("Entries da processare:", entries);
        
        const list = entries.map(([sessionId, entries]) => {
          console.log(`Processando sessione ${sessionId} con ${entries.length} entries`);
          const first = entries[0] || {};
          return {
            sessionId,
            title: first.title || 'Notebook senza titolo',
            createdAt: first.timestamp,
            prompt: first.system_prompt,
            sources: [...new Set(entries.map(e => e.source).filter(Boolean))],
          };
        }).filter(notebook => {
          const isValid = notebook.sessionId !== 'unknown';
          console.log(`Sessione ${notebook.sessionId}: ${isValid ? 'VALIDA' : 'FILTRATA (unknown)'}`);
          return isValid;
        });
        
        console.log("Lista notebooks finale processata:", list);
        console.log("Numero notebooks da mostrare:", list.length);
        setNotebooks(list);
        console.log("State setNotebooks chiamato con:", list);
        console.log("=== FINE CARICAMENTO NOTEBOOKS ===");
      })
      .catch(error => {
        console.error('Errore durante il caricamento dei notebook:', error);
        console.error('Error response:', error.response);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadNotebooks();
  }, []);

  const handleCreateSuccess = (sessionId) => {
    setShowCreateDialog(false);
    loadNotebooks(); // Ricarica la lista
    
    // Apri il nuovo notebook se richiesto
    if (sessionId) {
      onOpenNotebook(sessionId);
    }
  };

  const handleManageSources = (sessionId, e) => {
    e.stopPropagation(); // Previene l'apertura del notebook
    setSelectedNotebookId(sessionId);
    setShowSourcesManager(true);
  };

  const handleDeleteNotebook = async (sessionId, notebookTitle) => {
    console.log("=== INIZIO ELIMINAZIONE NOTEBOOK ===");
    console.log("Session ID:", sessionId);
    console.log("Titolo:", notebookTitle);
    
    if (!sessionId || sessionId === 'unknown') {
      console.error('ID sessione non valido:', sessionId);
      alert('Errore: ID sessione non valido');
      return;
    }
    
    if (!window.confirm(`Sei sicuro di voler eliminare il notebook "${notebookTitle}"? Questa azione non può essere annullata.`)) {
      console.log("Eliminazione annullata dall'utente");
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const deleteUrl = `${config.BACKEND_URL}/sessions/${sessionId}`;
      console.log("URL eliminazione:", deleteUrl);
      console.log("Token presente:", token ? "Sì" : "No");
      
      console.log("Invio richiesta DELETE...");
      const response = await axios.delete(deleteUrl, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log("Risposta DELETE ricevuta:");
      console.log("Status:", response.status);
      console.log("Data:", response.data);
      
      if (response.status === 200) {
        console.log("Eliminazione completata con successo");
        // Ricarica la lista dei notebook
        console.log("Ricaricamento lista notebook...");
        loadNotebooks();
        console.log("=== FINE ELIMINAZIONE NOTEBOOK (SUCCESS) ===");
      } else {
        console.warn("Status code inaspettato:", response.status);
      }

    } catch (error) {
      console.error('=== ERRORE ELIMINAZIONE NOTEBOOK ===');
      console.error('Errore completo:', error);
      console.error('Response status:', error.response?.status);
      console.error('Response data:', error.response?.data);
      console.error('Response headers:', error.response?.headers);
      
      let errorMessage = 'Errore durante l\'eliminazione del notebook. Riprova.';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      alert(errorMessage);
      console.log("=== FINE ELIMINAZIONE NOTEBOOK (ERROR) ===");
    }
  };

  // Se stiamo gestendo i documenti, mostra DocumentsManager
  if (showDocumentsManager) {
    return (
      <DocumentsManager 
        onBack={() => setShowDocumentsManager(false)}
      />
    );
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-bold mb-6 text-blue-700">Notebooks (Chat RAG)</h2>
      {loading ? <div>Caricamento...</div> : (
        notebooks.length === 0 ? (
          <div className="text-gray-500 text-lg text-center py-12">Non hai ancora notebook salvati. Crea il tuo primo notebook!</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {notebooks.map(nb => (
              <div key={nb.sessionId} 
                className="p-6 bg-white rounded-lg shadow hover:shadow-lg border-2 border-blue-200 hover:border-blue-500 transition-all relative">
                {/* Pulsanti in alto a destra */}
                <div className="absolute top-2 right-2 flex space-x-1">
                  <button
                    onClick={(e) => handleManageSources(nb.sessionId, e)}
                    className="bg-blue-500 hover:bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-xs font-bold"
                    title="Gestisci fonti"
                  >
                    📂
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteNotebook(nb.sessionId, nb.title);
                    }}
                    className="bg-red-500 hover:bg-red-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold"
                    title="Elimina notebook"
                  >
                    ×
                  </button>
                </div>
                
                {/* Contenuto del notebook - cliccabile */}
                <div 
                  onClick={() => onOpenNotebook(nb.sessionId)}
                  className="cursor-pointer flex flex-col items-start text-left h-full"
                >
                  <div className="font-bold text-lg mb-2 text-blue-700 pr-20">{nb.title}</div>
                  <div className="text-xs text-gray-500 mb-1">Creato: {nb.createdAt ? new Date(nb.createdAt).toLocaleString() : 'N/D'}</div>
                  <div className="mb-2"><span className="font-semibold">Prompt:</span> <span className="text-gray-700">{nb.prompt || <em>nessuno</em>}</span></div>
                  <div className="mb-2"><span className="font-semibold">Fonti:</span> <span className="text-gray-700">{nb.sources.length ? nb.sources.join(', ') : <em>nessuna</em>}</span></div>
                  <span className="mt-auto text-blue-600 font-semibold">Apri notebook →</span>
                </div>
              </div>
            ))}
          </div>
        )
      )}
      <div className="mt-8 flex flex-wrap gap-4">
        <button 
          className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-bold text-lg shadow" 
          onClick={() => setShowCreateDialog(true)}
        >
          ➕ Nuovo Notebook
        </button>
        <button 
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-bold text-lg shadow" 
          onClick={() => setShowDocumentsManager(true)}
        >
          📄 Gestisci Documenti
        </button>
      </div>
      
      {showCreateDialog && (
        <NewNotebookDialog 
          onSuccess={handleCreateSuccess}
          onCancel={() => setShowCreateDialog(false)}
        />
      )}

      {showSourcesManager && (
        <NotebookSourcesManager
          sessionId={selectedNotebookId}
          isOpen={showSourcesManager}
          onClose={() => {
            setShowSourcesManager(false);
            setSelectedNotebookId(null);
          }}
        />
      )}
    </div>
  );
}

export default NotebooksPage;
