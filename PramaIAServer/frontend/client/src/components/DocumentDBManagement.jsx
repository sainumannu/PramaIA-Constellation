import React, { useState, useEffect } from 'react';
import { API_URLS, createFetchConfig } from '../utils/apiUtils';

const DocumentDBManagement = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [resetLoading, setResetLoading] = useState({});
  const [documentList, setDocumentList] = useState(null);
  const [showDocumentList, setShowDocumentList] = useState(false);

  const fetchDocumentList = async () => {
    try {
      const response = await fetch(
        API_URLS.VECTORSTORE_DIRECT_DOCUMENTS, 
        createFetchConfig()
      );
      const data = await response.json();
      setDocumentList(data);
    } catch (error) {
      console.error('Errore nel recuperare documenti dal database:', error);
      setDocumentList({ error: error.message });
    }
  };

  const fetchStatus = async () => {
    try {
      const response = await fetch(
        API_URLS.VECTORSTORE_DIRECT_STATS, 
        createFetchConfig()
      );
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error('Errore nel recuperare lo stato del database documenti:', error);
      setStatus({ error: error.message });
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleReset = async () => {
    if (!window.confirm('Sei sicuro di voler resettare il database documenti? Questa operazione non può essere annullata.')) {
      return;
    }

    setResetLoading(prev => ({ ...prev, documents: true }));
    
    try {
      const response = await fetch(
        API_URLS.VECTORSTORE_DIRECT + 'api/database-management/documents/reset',
        createFetchConfig('POST')
      );
      
      const result = await response.json();
      
      if (result.success) {
        alert('Reset del database documenti completato con successo!');
        await fetchStatus(); // Aggiorna lo stato
      } else {
        alert(`Errore durante il reset del database documenti: ${result.message}`);
      }
    } catch (error) {
      console.error('Errore durante reset database documenti:', error);
      alert('Errore durante il reset del database documenti');
    } finally {
      setResetLoading(prev => ({ ...prev, documents: false }));
    }
  };

  const handleBackup = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        API_URLS.VECTORSTORE_DIRECT + '/backup', 
        createFetchConfig('POST')
      );
      
      const result = await response.json();
      
      if (result.success) {
        alert(`Backup del database documenti creato con successo in: ${result.details.backup_path}`);
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
        <h2 className="text-2xl font-bold mb-4">Gestione Database Documenti</h2>
        <p>Caricamento stato database...</p>
      </div>
    );
  }

  if (status.error) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold mb-4">Gestione Database Documenti</h2>
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
          <h2 className="text-2xl font-bold text-gray-900">Gestione Database Documenti (SQLite)</h2>
          <p className="text-gray-600">Monitora e gestisci i metadati dei documenti nel database SQLite</p>
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

      {/* Stato Database Documenti */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow border">
          <h3 className="font-semibold text-lg mb-2">Database SQLite Metadati</h3>
          {status.error ? (
            <p className="text-red-500">{status.error}</p>
          ) : (
            <div>
              <p className="text-2xl font-bold text-blue-600">
                {status.sqlite_documents || 0} documenti
              </p>
              <p className="text-sm text-gray-500">
                metadati nel database SQLite
              </p>
              <span className={`inline-block px-2 py-1 rounded text-xs ${
                status.status === 'ok' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {status.status || 'status sconosciuto'}
              </span>
            </div>
          )}
        </div>

        <div className="bg-white p-4 rounded-lg shadow border">
          <h3 className="font-semibold text-lg mb-2">Statistiche Database SQLite</h3>
          <div className="grid grid-cols-1 gap-2">
            <div>
              <p className="text-sm text-gray-500">Metadati oggi:</p>
              <p className="text-xl font-bold text-green-600">{status.documents_today || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Lista documenti */}
      <div className="bg-white p-6 rounded-lg shadow border mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-semibold">📄 Metadati Documenti (SQLite)</h3>
          <button 
            onClick={() => {
              setShowDocumentList(!showDocumentList);
              if (!showDocumentList && !documentList) {
                fetchDocumentList();
              }
            }}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            {showDocumentList ? 'Nascondi Lista' : 'Mostra Lista'}
          </button>
        </div>

        {showDocumentList && (
          <div>
            {!documentList ? (
              <p>Caricamento documenti...</p>
            ) : documentList.error ? (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                Errore: {documentList.error}
              </div>
            ) : (
              <div>
                <div className="mb-4 p-3 bg-blue-50 rounded">
                  <p className="font-semibold">Totale metadati nel database SQLite: {documentList.total || documentList.documents?.length || 0}</p>
                  <p className="text-sm text-gray-600">{documentList.message || ''}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Nota: Questa lista mostra i documenti dal VectorStore. Per una separazione completa, 
                    dovrebbe essere implementato un endpoint dedicato per il database SQLite metadati.
                  </p>
                </div>

                {documentList.documents && documentList.documents.length > 0 ? (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome File/ID</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Collection</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data Creazione</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dimensione</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {documentList.documents.map((doc) => (
                          <tr key={doc.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 text-sm font-mono">
                              <div className="flex items-center space-x-2">
                                <code className="bg-gray-100 px-2 py-1 rounded text-xs select-all break-all max-w-xs">
                                  {doc.id}
                                </code>
                                <button 
                                  onClick={() => navigator.clipboard.writeText(doc.id)}
                                  className="text-blue-500 hover:text-blue-700 text-xs"
                                  title="Copia ID"
                                >
                                  📋
                                </button>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              {doc.filename || doc.metadata?.filename || doc.metadata?.source || doc.id?.split('_')[0] || 'Test Document'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {doc.collection || 'default'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {doc.created_at ? new Date(doc.created_at).toLocaleString('it-IT') : 'N/A'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {doc.content ? `${Math.round(doc.content.length / 1024 * 100) / 100} KB` : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-gray-500">Nessun documento trovato nel database</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Sezione Reset */}
      <div className="bg-white p-6 rounded-lg shadow border">
        <h3 className="text-xl font-semibold mb-4 text-red-600">🗑️ Operazioni di Reset</h3>
        <div className="p-4 border rounded">
          <h4 className="font-semibold mb-2">Reset Database SQLite</h4>
          <p className="text-sm text-gray-600 mb-3">
            Cancella tutti i metadati dei documenti dal database SQLite. Non elimina i documenti fisici né i vettori.
          </p>
          <button 
            onClick={handleReset}
            disabled={resetLoading.documents}
            className="w-full px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
          >
            {resetLoading.documents ? 'Resettando...' : 'Reset Database SQLite'}
          </button>
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

export default DocumentDBManagement;
