import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config/appConfig';

const VectorstoreSettings = () => {
  const [settings, setSettings] = useState({
    schedule_enabled: true,
    schedule_time: "03:00",
    chroma_host: "localhost",
    chroma_port: 8000,
    max_worker_threads: 4,
    batch_size: 100
  });
  
  const [loading, setLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [status, setStatus] = useState(null);

  // Recupera le impostazioni attuali
  const fetchSettings = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/database-management/vectorstore/settings`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || 'fake-token'}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setSettings(data);
    } catch (error) {
      console.error('Errore nel recuperare le impostazioni:', error);
      setError(`Impossibile recuperare le impostazioni: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Recupera lo stato del servizio
  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/database-management/vectorstore/status`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || 'fake-token'}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error('Errore nel recuperare lo stato del servizio:', error);
      setStatus({ status: "error", error: error.message });
    }
  };

  // Salva le impostazioni
  const saveSettings = async () => {
    setSaveLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/database-management/vectorstore/settings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || 'fake-token'}`
        },
        body: JSON.stringify(settings)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setSuccess("Impostazioni salvate con successo");
      
      // Aggiorna lo stato del servizio
      fetchStatus();
    } catch (error) {
      console.error('Errore nel salvare le impostazioni:', error);
      setError(`Impossibile salvare le impostazioni: ${error.message}`);
    } finally {
      setSaveLoading(false);
    }
  };

  // Avvia una riconciliazione manuale
  const startReconciliation = async () => {
    if (!window.confirm('Sei sicuro di voler avviare una riconciliazione manuale?\nQuesto processo potrebbe richiedere tempo per completarsi.')) {
      return;
    }
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/database-management/vectorstore/reconciliation/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || 'fake-token'}`
        },
        body: JSON.stringify({
          delete_missing: window.confirm('Vuoi eliminare i documenti non più presenti nel filesystem?')
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setSuccess(`Riconciliazione avviata con successo. Job ID: ${data.job_id}`);
      
      // Aggiorna lo stato del servizio
      fetchStatus();
    } catch (error) {
      console.error('Errore nell\'avviare la riconciliazione:', error);
      setError(`Impossibile avviare la riconciliazione: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Carica le impostazioni e lo stato all'avvio
  useEffect(() => {
    fetchSettings();
    fetchStatus();
  }, []);

  // Gestisce i cambiamenti nei campi del form
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // Gestisce l'invio del form
  const handleSubmit = (e) => {
    e.preventDefault();
    saveSettings();
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Configurazione VectorstoreService</h2>
        <p className="text-gray-600">Gestisci le impostazioni del servizio di vectorstore e la riconciliazione</p>
      </div>

      {/* Stato del servizio */}
      <div className="bg-white p-6 rounded-lg shadow border mb-6">
        <h3 className="text-xl font-semibold mb-4">Stato del Servizio</h3>
        
        {!status ? (
          <p>Caricamento stato...</p>
        ) : status.error ? (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <p className="font-bold">Errore di connessione</p>
            <p>{status.error}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className={`p-4 rounded ${status.status === 'healthy' ? 'bg-green-50' : 'bg-yellow-50'}`}>
              <h4 className="font-semibold">Stato</h4>
              <p className={`text-lg font-bold ${status.status === 'healthy' ? 'text-green-600' : 'text-yellow-600'}`}>
                {status.status === 'healthy' ? 'Operativo' : 'Parzialmente operativo'}
              </p>
              <p className="text-sm">Versione: {status.version}</p>
            </div>
            
            <div className="p-4 rounded bg-blue-50">
              <h4 className="font-semibold">ChromaDB</h4>
              <p className={`text-lg font-bold ${status.dependencies?.chroma?.status === 'healthy' ? 'text-blue-600' : 'text-red-600'}`}>
                {status.dependencies?.chroma?.status === 'healthy' ? 'Connesso' : 'Non connesso'}
              </p>
              <p className="text-sm">
                {status.dependencies?.chroma?.details?.host || 'N/A'}:{status.dependencies?.chroma?.details?.port || 'N/A'}
              </p>
            </div>
            
            <div className="p-4 rounded bg-purple-50">
              <h4 className="font-semibold">Scheduler</h4>
              <p className={`text-lg font-bold ${status.scheduler_enabled ? 'text-purple-600' : 'text-gray-600'}`}>
                {status.scheduler_enabled ? 'Attivo' : 'Disattivato'}
              </p>
              <p className="text-sm">
                {status.scheduler_enabled ? `Prossima esecuzione: ${status.next_reconciliation || 'N/A'}` : 'Riconciliazione pianificata disattivata'}
              </p>
            </div>
          </div>
        )}
        
        <div className="mt-4">
          <button
            onClick={fetchStatus}
            disabled={loading}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 mr-3"
          >
            Aggiorna Stato
          </button>
          
          <button
            onClick={startReconciliation}
            disabled={loading || (status && status.status !== 'healthy')}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
          >
            Avvia Riconciliazione Manuale
          </button>
        </div>
        
        {error && (
          <div className="mt-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}
        
        {success && (
          <div className="mt-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            {success}
          </div>
        )}
      </div>

      {/* Form di configurazione */}
      <div className="bg-white p-6 rounded-lg shadow border">
        <h3 className="text-xl font-semibold mb-4">Impostazioni</h3>
        
        <form onSubmit={handleSubmit}>
          {/* Scheduler */}
          <div className="mb-6">
            <h4 className="font-semibold text-lg mb-3">Scheduler di Riconciliazione</h4>
            
            <div className="mb-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="schedule_enabled"
                  name="schedule_enabled"
                  checked={settings.schedule_enabled}
                  onChange={handleChange}
                  className="h-4 w-4 text-blue-600 rounded"
                />
                <label htmlFor="schedule_enabled" className="ml-2 block text-sm text-gray-900">
                  Abilita riconciliazione pianificata
                </label>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Quando abilitata, la riconciliazione verrà eseguita automaticamente all'orario specificato
              </p>
            </div>
            
            <div className="mb-4">
              <label htmlFor="schedule_time" className="block text-sm font-medium text-gray-700">
                Orario di riconciliazione
              </label>
              <input
                type="time"
                id="schedule_time"
                name="schedule_time"
                value={settings.schedule_time}
                onChange={handleChange}
                disabled={!settings.schedule_enabled}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
              <p className="text-xs text-gray-500 mt-1">
                Orario giornaliero in cui verrà eseguita la riconciliazione (formato 24h)
              </p>
            </div>
          </div>
          
          {/* ChromaDB */}
          <div className="mb-6">
            <h4 className="font-semibold text-lg mb-3">Configurazione ChromaDB</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="chroma_host" className="block text-sm font-medium text-gray-700">
                  Host ChromaDB
                </label>
                <input
                  type="text"
                  id="chroma_host"
                  name="chroma_host"
                  value={settings.chroma_host}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
              
              <div>
                <label htmlFor="chroma_port" className="block text-sm font-medium text-gray-700">
                  Porta ChromaDB
                </label>
                <input
                  type="number"
                  id="chroma_port"
                  name="chroma_port"
                  value={settings.chroma_port}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
            </div>
          </div>
          
          {/* Impostazioni Avanzate */}
          <div className="mb-6">
            <h4 className="font-semibold text-lg mb-3">Impostazioni Avanzate</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="max_worker_threads" className="block text-sm font-medium text-gray-700">
                  Thread di Lavoro Massimi
                </label>
                <input
                  type="number"
                  id="max_worker_threads"
                  name="max_worker_threads"
                  value={settings.max_worker_threads}
                  onChange={handleChange}
                  min="1"
                  max="16"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Numero massimo di thread per le operazioni di riconciliazione (1-16)
                </p>
              </div>
              
              <div>
                <label htmlFor="batch_size" className="block text-sm font-medium text-gray-700">
                  Dimensione Batch
                </label>
                <input
                  type="number"
                  id="batch_size"
                  name="batch_size"
                  value={settings.batch_size}
                  onChange={handleChange}
                  min="10"
                  max="1000"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Numero di documenti elaborati in un singolo batch (10-1000)
                </p>
              </div>
            </div>
          </div>
          
          {/* Pulsanti */}
          <div className="flex justify-end">
            <button
              type="button"
              onClick={fetchSettings}
              disabled={loading}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50 mr-3"
            >
              Annulla Modifiche
            </button>
            
            <button
              type="submit"
              disabled={saveLoading}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            >
              {saveLoading ? 'Salvataggio...' : 'Salva Impostazioni'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default VectorstoreSettings;
