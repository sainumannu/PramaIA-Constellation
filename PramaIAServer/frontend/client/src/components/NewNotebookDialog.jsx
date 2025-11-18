import React, { useState } from 'react';
import axios from 'axios';
import config from '../config';

function NewNotebookDialog({ onSuccess, onCancel }) {
  const [title, setTitle] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  const handleCreate = async () => {
    if (!title.trim()) {
      setError('Il titolo è obbligatorio');
      return;
    }

    setCreating(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(`${config.BACKEND_URL}/sessions/new`, {
        title: title,
        model: 'gpt-4',
        mode: 'rag',
        system_prompt: `Benvenuto nel notebook "${title}"!`
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (res.data.session_id) {
        // Verifica che la sessione sia pronta
        const checkStatus = async () => {
          try {
            const statusRes = await axios.get(
              `${config.BACKEND_URL}/sessions/${res.data.session_id}/status`,
              {
                headers: {
                  'Authorization': `Bearer ${token}`
                }
              }
            );
            return statusRes.data.status === 'ready';
          } catch (error) {
            return false;
          }
        };

        // Polling con backoff esponenziale
        for (let i = 0; i < 5; i++) {
          const isReady = await checkStatus();
          if (isReady) {
            onSuccess(res.data.session_id);
            return;
          }
          if (i < 4) {
            await new Promise(resolve => setTimeout(resolve, 100 * Math.pow(2, i)));
          }
        }
        throw new Error('Timeout nel creare il notebook');
      }
    } catch (err) {
      console.error('Errore creazione notebook:', err);
      setError(err.response?.data?.detail || 'Errore nella creazione del notebook');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg shadow-xl max-w-md w-full">
        <h2 className="text-xl font-bold mb-4">Nuovo Notebook</h2>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Titolo
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Inserisci il titolo del notebook"
            disabled={creating}
          />
        </div>

        {error && (
          <div className="mb-4 text-red-600 text-sm">{error}</div>
        )}

        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
            disabled={creating}
          >
            Annulla
          </button>
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            disabled={creating || !title.trim()}
          >
            {creating ? 'Creazione...' : 'Crea Notebook'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default NewNotebookDialog;
