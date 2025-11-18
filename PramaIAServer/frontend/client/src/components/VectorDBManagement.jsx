import React, { useState, useEffect } from 'react';
import { API_URLS, createFetchConfig } from '../utils/apiUtils';

const VectorDBManagement = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [resetLoading, setResetLoading] = useState({});
  const [vectorDocs, setVectorDocs] = useState(null);
  const [showVectorDocs, setShowVectorDocs] = useState(false);
  const [documentPreviews, setDocumentPreviews] = useState({});
  const [previewLoading, setPreviewLoading] = useState({});

  const fetchVectorStoreDocuments = async () => {
    try {
      const response = await fetch(
        API_URLS.VECTORSTORE_DIRECT_DOCUMENTS, 
        createFetchConfig()
      );
      const data = await response.json();
      setVectorDocs(data);
      
      // Se ci sono documenti, inizia a caricare le anteprime per i primi 5
      if (data && data.documents && data.documents.length > 0) {
        // Inizia a caricare le anteprime per i primi 5 documenti
        const docsToPreload = data.documents.slice(0, 5);
        docsToPreload.forEach(doc => {
          fetchDocumentContent(doc.id);
        });
      }
    } catch (error) {
      console.error('Errore nel recuperare documenti vector store:', error);
      setVectorDocs({ error: error.message });
    }
  };

  const fetchDocumentContent = async (documentId) => {
    if (documentPreviews[documentId] || previewLoading[documentId]) {
      return; // Già caricato o in caricamento
    }
    setPreviewLoading(prev => ({ ...prev, [documentId]: true }));
    try {
      // Chiamata diretta all'API per ottenere il contenuto completo del documento
      const url = `${API_URLS.VECTORSTORE_DIRECT_DOCUMENTS}/${documentId}`;
      const response = await fetch(url, createFetchConfig());
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const doc = await response.json();
      if (doc && doc.content) {
        const previewText = doc.content.length > 500 
          ? `${doc.content.substring(0, 500)}...` 
          : doc.content;
        setDocumentPreviews(prev => ({
          ...prev,
          [documentId]: {
            text: previewText,
            source: "vectorstore_direct",
            sourceLabel: "📊 Fonte: VectorStore Diretto"
          }
        }));
      } else {
        setDocumentPreviews(prev => ({
          ...prev,
          [documentId]: {
            text: "Contenuto non disponibile in anteprima",
            source: "error",
            sourceLabel: "❌ Errore: Contenuto non disponibile"
          }
        }));
      }
    } catch (error) {
      console.error(`Errore nel recuperare contenuto documento ${documentId}:`, error);
      setDocumentPreviews(prev => ({
        ...prev,
        [documentId]: {
          text: "Errore nel caricamento dell'anteprima",
          source: "error",
          sourceLabel: "❌ Errore di caricamento"
        }
      }));
    } finally {
      setPreviewLoading(prev => ({ ...prev, [documentId]: false }));
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
      console.error('Errore nel recuperare lo stato del vector store:', error);
      setStatus({ error: error.message });
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleReset = async () => {
    if (!window.confirm('Sei sicuro di voler resettare il vector store? Questa operazione non può essere annullata.')) {
      return;
    }

    setResetLoading(prev => ({ ...prev, vectorstore: true }));
    
    try {
      const response = await fetch(
        API_URLS.VECTORSTORE_DIRECT + 'api/database-management/vectorstore/reset',
        createFetchConfig('POST')
      );
      
      const result = await response.json();
      
      if (result.success) {
        alert('Reset del vector store completato con successo!');
        await fetchStatus(); // Aggiorna lo stato
      } else {
        alert(`Errore durante il reset del vector store: ${result.message}`);
      }
    } catch (error) {
      console.error('Errore durante reset vector store:', error);
      alert('Errore durante il reset del vector store');
    } finally {
      setResetLoading(prev => ({ ...prev, vectorstore: false }));
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
        alert(`Backup del vector store creato con successo in: ${result.details.backup_path}`);
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

  const getDocumentPreview = (doc) => {
    if (documentPreviews[doc.id]) {
      return documentPreviews[doc.id];
    }
    
    if (previewLoading[doc.id]) {
      return {
        text: "⏳ Caricamento anteprima in corso...",
        source: "loading",
        sourceLabel: "⏳ Caricamento..."
      };
    }
    
    // Se la preview non è stata ancora caricata, inizia a caricarla
    fetchDocumentContent(doc.id);
    return {
      text: "⏳ Caricamento anteprima in corso...",
      source: "loading",
      sourceLabel: "⏳ Caricamento..."
    };
  };

  if (!status) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold mb-4">Gestione Vector Store</h2>
        <p>Caricamento stato vector store...</p>
      </div>
    );
  }

  if (status.error) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold mb-4">Gestione Vector Store</h2>
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
          <h2 className="text-2xl font-bold text-gray-900">Gestione Vector Store</h2>
          <p className="text-gray-600">Monitora e gestisci il vector store per la ricerca semantica</p>
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

      {/* Stato Vector Store */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow border">
          <h3 className="font-semibold text-lg mb-2">Vector Store</h3>
          {status.error ? (
            <p className="text-red-500">{status.error}</p>
          ) : (
            <div>
              <p className="text-2xl font-bold text-green-600">
                {status.documents_total || 0} documenti
              </p>
              <p className="text-sm text-gray-500">
                nel VectorStore (solo contenuto testuale)
              </p>
              <span className={`inline-block px-2 py-1 rounded text-xs ${
                status.status === 'ok' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {status.status || 'status sconosciuto'}
              </span>
              <p className="text-xs text-orange-600 mt-1">
                ⚠️ Nota: I file binari non dovrebbero essere nel VectorStore
              </p>
            </div>
          )}
        </div>

        <div className="bg-white p-4 rounded-lg shadow border">
          <h3 className="font-semibold text-lg mb-2">Statistiche Vector Store</h3>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <p className="text-sm text-gray-500">Documenti oggi:</p>
              <p className="text-xl font-bold text-green-600">{status.documents_today || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Dimensione media:</p>
              <p className="text-xl font-bold text-purple-600">
                {status.avg_chunk_size ? `${status.avg_chunk_size.toFixed(2)} KB` : 'N/A'}
              </p>
            </div>
          </div>
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
                            <strong>ID:</strong> {doc.id}
                          </div>
                        </div>
                        <div className="mt-2">
                          <div className="flex justify-between items-center">
                            <strong>Anteprima contenuto:</strong>
                            {previewLoading[doc.id] && (
                              <span className="text-xs text-blue-500">Caricamento...</span>
                            )}
                          </div>
                          <div className="text-xs bg-white p-2 rounded mt-1 max-h-20 overflow-y-auto">
                            {getDocumentPreview(doc).text}
                          </div>
                          {documentPreviews[doc.id] && documentPreviews[doc.id].sourceLabel && (
                            <div className="text-xs mt-1 text-gray-500 italic">
                              {documentPreviews[doc.id].sourceLabel}
                            </div>
                          )}
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
        <div className="p-4 border rounded">
          <h4 className="font-semibold mb-2">Reset Vector Store</h4>
          <p className="text-sm text-gray-600 mb-3">
            Cancella tutti i documenti vettorizzati. Questa operazione è utile per risolvere problemi con il ChromaDB.
          </p>
          <button 
            onClick={handleReset}
            disabled={resetLoading.vectorstore}
            className="w-full px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
          >
            {resetLoading.vectorstore ? 'Resettando...' : 'Reset Vector Store'}
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

export default VectorDBManagement;
