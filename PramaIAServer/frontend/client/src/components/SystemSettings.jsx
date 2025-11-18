import React, { useState, useEffect } from 'react';
import axios from 'axios';
import config from '../config';

const SystemSettings = () => {
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [editValues, setEditValues] = useState({});

  // Carica le impostazioni all'avvio
  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${config.BACKEND_URL}/api/settings/config`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      setSettings(response.data);
      
      // Inizializza i valori di modifica con i valori correnti
      const initialEditValues = {};
      Object.entries(response.data).forEach(([key, setting]) => {
        initialEditValues[key] = setting.value;
      });
      setEditValues(initialEditValues);
      
      setLoading(false);
    } catch (err) {
      console.error('Errore nel recupero delle impostazioni:', err);
      setError(err.response?.data?.detail || 'Errore nel caricamento delle impostazioni');
      setLoading(false);
    }
  };

  const handleInputChange = (key, value) => {
    setEditValues(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSaveSetting = async (key) => {
    setLoading(true);
    setMessage('');
    setError('');
    
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${config.BACKEND_URL}/api/settings/config/${key}`,
        {
          key: key,
          value: editValues[key]
        },
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      setMessage(`Impostazione "${key}" aggiornata con successo!`);
      // Ricarica le impostazioni per mostrare il valore aggiornato
      fetchSettings();
      
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      console.error('Errore nel salvataggio dell\'impostazione:', err);
      setError(err.response?.data?.detail || `Errore nell'aggiornamento di ${key}`);
      setTimeout(() => setError(''), 5000);
    } finally {
      setLoading(false);
    }
  };

  const renderSettingInput = (key, setting) => {
    switch (setting.type) {
      case 'integer':
        return (
          <input
            type="number"
            value={editValues[key]}
            onChange={(e) => handleInputChange(key, parseInt(e.target.value))}
            className="border border-gray-300 rounded px-3 py-2 w-full"
            disabled={!setting.is_editable || loading}
          />
        );
      case 'boolean':
        return (
          <select
            value={editValues[key].toString()}
            onChange={(e) => handleInputChange(key, e.target.value === 'true')}
            className="border border-gray-300 rounded px-3 py-2 w-full"
            disabled={!setting.is_editable || loading}
          >
            <option value="true">Abilitato</option>
            <option value="false">Disabilitato</option>
          </select>
        );
      default:
        return (
          <input
            type="text"
            value={editValues[key]}
            onChange={(e) => handleInputChange(key, e.target.value)}
            className="border border-gray-300 rounded px-3 py-2 w-full"
            disabled={!setting.is_editable || loading}
          />
        );
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-semibold">⚙️ Impostazioni di Sistema</h3>
        <button
          onClick={fetchSettings}
          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
          disabled={loading}
        >
          {loading ? 'Caricamento...' : '🔄 Aggiorna'}
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {message && (
        <div className="mb-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          {message}
        </div>
      )}

      {loading && !error ? (
        <div className="text-center py-10">
          <p className="text-gray-500">Caricamento impostazioni...</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="mb-4 bg-blue-50 p-4 rounded-lg">
            <p className="text-sm text-blue-800">
              Queste impostazioni consentono di personalizzare il comportamento del sistema.
              Le modifiche avranno effetto immediato su tutti i componenti.
            </p>
          </div>

          {Object.keys(settings).length === 0 ? (
            <p className="text-gray-500 text-center py-5">
              Nessuna impostazione disponibile.
            </p>
          ) : (
            <div className="divide-y">
              {Object.entries(settings).map(([key, setting]) => (
                <div key={key} className="py-4">
                  <div className="flex justify-between items-center mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      {setting.description || key}
                    </label>
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {setting.type}
                    </span>
                  </div>
                  
                  <div className="flex space-x-3">
                    {renderSettingInput(key, setting)}
                    
                    <button
                      onClick={() => handleSaveSetting(key)}
                      className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
                      disabled={!setting.is_editable || loading || editValues[key] === setting.value}
                    >
                      Salva
                    </button>
                  </div>
                  
                  {!setting.is_editable && (
                    <p className="text-xs text-orange-500 mt-1">
                      Questa impostazione non può essere modificata.
                    </p>
                  )}

                  <p className="text-xs text-gray-500 mt-1">
                    Valore attuale: <code className="bg-gray-100 px-1 py-0.5 rounded">{setting.value !== undefined ? String(setting.value) : 'N/D'}</code>
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SystemSettings;
