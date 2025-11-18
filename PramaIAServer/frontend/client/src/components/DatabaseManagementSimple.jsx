import React, { useState, useEffect } from 'react';
import { API_URLS, createFetchConfig } from '../utils/apiUtils';

const DatabaseManagement = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [resetLoading, setResetLoading] = useState({});
  const [vectorDocs, setVectorDocs] = useState(null);
  const [showVectorDocs, setShowVectorDocs] = useState(false);

  const fetchVectorStoreDocuments = async () => {
    try {
      const response = await fetch(
        `${API_URLS.DATABASE_MANAGEMENT}/vectorstore/documents`, 
        createFetchConfig()
      );
      const data = await response.json();
      setVectorDocs(data);
    } catch (error) {
      console.error('Errore nel recuperare documenti vector store:', error);
      setVectorDocs({ error: error.message });
    }
  };

  const fetchStatus = async () => {
    try {
      const response = await fetch(
        `${API_URLS.DATABASE_MANAGEMENT}/status`, 
        createFetchConfig()
      );
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error('Errore nel recuperare lo stato dei database:', error);
      setStatus({ error: error.message });
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleReset = async (type) => {
    if (!window.confirm(`Sei sicuro di voler resettare ${type}? Questa operazione non può essere annullata.`)) {
      return;
    }

    setResetLoading(prev => ({ ...prev, [type]: true }));
    
    try {
      const response = await fetch(
        `${API_URLS.DATABASE_MANAGEMENT}/reset/${type}`, 
        createFetchConfig('POST')
      );
      
      const result = await response.json();
      
      if (result.success) {
        alert(`Reset di ${type} completato con successo!`);
        await fetchStatus(); // Aggiorna lo stato
      } else {
        alert(`Errore durante il reset di ${type}: ${result.message}`);
      }
    } catch (error) {
      console.error(`Errore durante reset ${type}:`, error);
      alert(`Errore durante il reset di ${type}`);
    } finally {
      setResetLoading(prev => ({ ...prev, [type]: false }));
    }
  };

  const handleBackup = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_URLS.DATABASE_MANAGEMENT}/backup/create`, 
        createFetchConfig('POST')
      );
      
      const result = await response.json();
      
      if (result.success) {
        alert(`Backup creato con successo in: ${result.details.backup_path}`);
      } else {
        alert(`Errore durante la creazione del backup: ${result.message}`);
      }
    } catch (error) {
      console.error('Errore durante creazione backup:', error);
      alert('Errore durante la creazione del backup');
    } finally {
      setLoading(false);
    }
  };

  if (!status) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold mb-4">Gestione Database</h2>
        <p>Caricamento stato database...</p>
      </div>
    );
  }

  if (status.error) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold mb-4">Gestione Database</h2>
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          Errore: {status.error}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Gestione Database</h2>
          <p className="text-gray-600">Monitora e gestisci i database del sistema</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={fetchStatus} 
            disabled={loading}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {loading ? 'Aggiornando...' : 'Aggiorna'}
          </button>
          <button 
            onClick={handleBackup}
            disabled={loading}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
          >
            {loading ? 'Creando...' : 'Crea Backup'}
          </button>
        </div>
      </div>

      {/* Stato Database */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Database Principale */}
        <div className="bg-white p-4 rounded-lg shadow border">
          <h3 className="font-semibold text-lg mb-2">Database Principale</h3>
          {status.main_database?.error ? (
            <p className="text-red-500">{status.main_database.error}</p>
          ) : (
            <div>
              <p className="text-2xl font-bold text-blue-600">
                {Object.keys(status.main_database?.tables || {}).length} tabelle
              </p>
              <p className="text-sm text-gray-500">
                {Math.round((status.main_database?.size_bytes || 0) / 1024)} KB
              </p>
            </div>
          )}
        </div>

        {/* Vector Store */}
        <div className="bg-white p-4 rounded-lg shadow border">
          <h3 className="font-semibold text-lg mb-2">Vector Store</h3>
          {status.vectorstore?.error ? (
            <p className="text-red-500">{status.vectorstore.error}</p>
          ) : (
            <div>
              <p className="text-2xl font-bold text-green-600">
                {status.vectorstore?.documents_in_index || 0}
              </p>
              <p className="text-sm text-gray-500">documenti vettorizzati</p>
              <span className={`inline-block px-2 py-1 rounded text-xs ${
                status.vectorstore?.status === 'ok' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {status.vectorstore?.status}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Dettagli Vector Store */}
      <div className="bg-white p-6 rounded-lg shadow border mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-semibold">🔍 Dettagli Vector Store</h3>
          <button 
            onClick={() => {
              setShowVectorDocs(!showVectorDocs);
              if (!showVectorDocs && !vectorDocs) {
                fetchVectorStoreDocuments();
              }
            }}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            {showVectorDocs ? 'Nascondi Dettagli' : 'Mostra Dettagli'}
          </button>
        </div>

        {showVectorDocs && (
          <div>
            {!vectorDocs ? (
              <p>Caricamento documenti...</p>
            ) : vectorDocs.error ? (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                Errore: {vectorDocs.error}
              </div>
            ) : (
              <div>
                <div className="mb-4 p-3 bg-blue-50 rounded">
                  <p className="font-semibold">Totale documenti nel vector store: {vectorDocs.total}</p>
                  <p className="text-sm text-gray-600">{vectorDocs.message}</p>
                </div>

                {vectorDocs.documents && vectorDocs.documents.length > 0 ? (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {vectorDocs.documents.map((doc, index) => (
                      <div key={index} className="border p-3 rounded bg-gray-50">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                          <div>
                            <strong>File:</strong> {doc.source_filename}
                          </div>
                          <div>
                            <strong>Pagina:</strong> {doc.page}
                          </div>
                          <div>
                            <strong>Ingested:</strong> {doc.ingest_time}
                          </div>
                          <div>
                            <strong>ID:</strong> {doc.id.substring(0, 20)}...
                          </div>
                        </div>
                        <div className="mt-2">
                          <strong>Anteprima contenuto:</strong>
                          <div className="text-xs bg-white p-2 rounded mt-1 max-h-20 overflow-y-auto">
                            {doc.content_preview}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">Nessun documento trovato nel vector store</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Sezione Reset */}
      <div className="bg-white p-6 rounded-lg shadow border">
        <h3 className="text-xl font-semibold mb-4 text-red-600">🗑️ Operazioni di Reset</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Reset Vector Store */}
          <div className="p-4 border rounded">
            <h4 className="font-semibold mb-2">Reset Vector Store</h4>
            <p className="text-sm text-gray-600 mb-3">
              Cancella tutti i documenti vettorizzati. Risolve problemi con ChromaDB vuoto.
            </p>
            <button 
              onClick={() => handleReset('vectorstore')}
              disabled={resetLoading.vectorstore}
              className="w-full px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
            >
              {resetLoading.vectorstore ? 'Resettando...' : 'Reset Vector Store'}
            </button>
          </div>

          {/* Reset Eventi PDF */}
          <div className="p-4 border rounded">
            <h4 className="font-semibold mb-2">Reset Eventi PDF Monitor</h4>
            <p className="text-sm text-gray-600 mb-3">
              Resetta contatori e eventi PDF. Risolve inconsistenze come "3 in coda".
            </p>
            <button 
              onClick={() => handleReset('pdf-monitor-events')}
              disabled={resetLoading['pdf-monitor-events']}
              className="w-full px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
            >
              {resetLoading['pdf-monitor-events'] ? 'Resettando...' : 'Reset Eventi PDF'}
            </button>
          </div>

          {/* Reset Completo */}
          <div className="p-4 border rounded">
            <h4 className="font-semibold mb-2">Reset Completo Sistema</h4>
            <p className="text-sm text-gray-600 mb-3">
              Resetta tutto: vector store, eventi PDF e contatori. Ripartenza da zero.
            </p>
            <button 
              onClick={() => handleReset('all')}
              disabled={resetLoading.all}
              className="w-full px-4 py-2 bg-red-700 text-white rounded hover:bg-red-800 disabled:opacity-50"
            >
              {resetLoading.all ? 'Resettando tutto...' : 'Reset Completo'}
            </button>
          </div>
        </div>
      </div>

      {/* Debug Info */}
      <div className="mt-6 bg-gray-100 p-4 rounded">
        <h4 className="font-semibold mb-2">Debug Info</h4>
        <pre className="text-xs overflow-auto">
          {JSON.stringify(status, null, 2)}
        </pre>
      </div>
    </div>
  );
};

export default DatabaseManagement;
