import React, { useState, useEffect } from 'react';
import { OLLAMA_DEFAULT_URL } from '../config/appConfig';
import axios from 'axios'; // Solo per istanza custom Ollama

function LLMConfig({ onSave }) {
  const [ollamaUrl, setOllamaUrl] = useState(() => localStorage.getItem('ollamaUrl') || OLLAMA_DEFAULT_URL);
  const [ollamaModels, setOllamaModels] = useState([]);
  const [selectedOllamaModel, setSelectedOllamaModel] = useState(() => localStorage.getItem('ollamaModel') || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!ollamaUrl) return;
    setLoading(true);
    setError('');
    const ollamaApi = axios.create({ baseURL: ollamaUrl });
    ollamaApi.post('/api/tags')
      .then(res => {
        setOllamaModels(res.data.models || []);
      })
      .catch(() => setError('Impossibile recuperare i modelli da Ollama.'))
      .finally(() => setLoading(false));
  }, [ollamaUrl]);

  const handleSave = () => {
    localStorage.setItem('ollamaUrl', ollamaUrl);
    localStorage.setItem('ollamaModel', selectedOllamaModel);
    if (onSave) onSave({ ollamaUrl, ollamaModel: selectedOllamaModel });
  };

  return (
    <div className="p-4 bg-white rounded shadow mb-4">
      <h3 className="font-bold mb-2 text-blue-700">Configurazione Ollama</h3>
      <div className="mb-2">
        <label className="block font-semibold mb-1">URL server Ollama:</label>
        <input type="text" value={ollamaUrl} onChange={e => setOllamaUrl(e.target.value)} className="p-2 border rounded w-full" />
      </div>
      <div className="mb-2">
        <label className="block font-semibold mb-1">Modello locale:</label>
        {loading ? <span>Caricamento modelli...</span> :
          <select value={selectedOllamaModel} onChange={e => setSelectedOllamaModel(e.target.value)} className="p-2 border rounded w-full">
            <option value="">-- Seleziona modello --</option>
            {ollamaModels.map(m => <option key={m.name} value={m.name}>{m.name}</option>)}
          </select>
        }
        {error && <div className="text-red-500 text-sm mt-1">{error}</div>}
      </div>
      <button onClick={handleSave} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">Salva configurazione</button>
    </div>
  );
}

export default LLMConfig;
