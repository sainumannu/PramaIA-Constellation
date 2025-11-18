import React, { useState, useEffect } from 'react';
import axios from 'axios';
import config from '../config';
import { useNavigate } from 'react-router-dom';
import NewNotebookDialog from './NewNotebookDialog';
// import RAGChat from './RAGChat'; // Temporaneamente commentato per risolvere errore

function NotebooksList() {
  const [notebooks, setNotebooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [selectedNotebook, setSelectedNotebook] = useState(null);
  const navigate = useNavigate();

  const loadNotebooks = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const res = await axios.get(`${config.BACKEND_URL}/sessions/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setNotebooks(res.data.sessions || []);
    } catch (err) {
      console.error('Errore caricamento notebook:', err);
      setError('Errore nel caricamento dei notebook');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotebooks();
  }, []);

  const handleDelete = async (sessionId) => {
    if (!window.confirm('Sei sicuro di voler eliminare questo notebook?')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${config.BACKEND_URL}/sessions/${sessionId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      await loadNotebooks();
    } catch (err) {
      console.error('Errore eliminazione notebook:', err);
      setError('Errore nell\'eliminazione del notebook');
    }
  };

  const handleNewSuccess = (sessionId) => {
    setShowNewDialog(false);
    setSelectedNotebook(sessionId);
  };

  if (selectedNotebook) {
    return (
      <div className="p-4">
        <div className="mb-4">
          <button 
            onClick={() => {
              setSelectedNotebook(null);
              loadNotebooks();
            }}
            className="bg-gray-300 px-4 py-2 rounded"
          >
            Torna ai Notebooks
          </button>
        </div>
        <div className="text-center text-gray-500">
          RAGChat temporaneamente disabilitato. Usa NotebooksPage per aprire i notebook.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">I tuoi Notebook</h1>
        <button
          onClick={() => setShowNewDialog(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Nuovo Notebook
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border-l-4 border-red-500 p-4">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {loading ? (
        <div>Caricamento notebook...</div>
      ) : notebooks.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">Non hai ancora creato nessun notebook</p>
          <button
            onClick={() => setShowNewDialog(true)}
            className="bg-blue-100 text-blue-700 px-4 py-2 rounded hover:bg-blue-200"
          >
            Crea il tuo primo notebook
          </button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {notebooks.map(notebook => (
            <div 
              key={notebook.session_id} 
              className="border rounded-lg p-4 bg-white shadow hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold text-lg">{notebook.title || 'Notebook senza titolo'}</h3>
                <button
                  onClick={() => handleDelete(notebook.session_id)}
                  className="text-red-500 hover:text-red-700"
                  title="Elimina notebook"
                >
                  ×
                </button>
              </div>
              <p className="text-sm text-gray-500 mb-3">
                Creato: {new Date(notebook.created_at).toLocaleString()}
              </p>
              <button
                onClick={() => setSelectedNotebook(notebook.session_id)}
                className="w-full bg-gray-100 text-gray-700 px-3 py-2 rounded hover:bg-gray-200"
              >
                Apri Notebook
              </button>
            </div>
          ))}
        </div>
      )}

      {showNewDialog && (
        <NewNotebookDialog
          onSuccess={handleNewSuccess}
          onCancel={() => setShowNewDialog(false)}
        />
      )}
    </div>
  );
}

export default NotebooksList;
