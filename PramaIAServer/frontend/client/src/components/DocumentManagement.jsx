import React, { useState, useEffect } from 'react';
import { API_BASE_URL, CHAT_BASE_URL } from '../config/appConfig';
import PDFMonitoringPanel from './DocumentMonitoringPanelWithSync';
import DatabaseManagementSimple from './DatabaseManagementSimple';
import VectorstoreSettings from './VectorstoreSettings';

// Componente per Elaborazione Documenti
const DocumentProcessing = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [vectorstoreStats, setVectorstoreStats] = useState({
    total: 0,
    today: 0,
    queue: 0
  });

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/database-management/documents`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || 'fake-token'}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setDocuments(data.files || []);
      setError(null);
    } catch (error) {
      console.error('Errore nel recuperare i documenti:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchVectorstoreStatistics = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/database-management/vectorstore/statistics`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || 'fake-token'}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setVectorstoreStats({
        total: data.total_documents || 0,
        today: data.documents_today || 0,
        queue: data.queue_size || 0
      });
      setError(null);
    } catch (error) {
      console.error('Errore nel recuperare le statistiche dal vectorstore:', error);
      // Non impostiamo l'errore qui per non bloccare l'interfaccia
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      await fetchDocuments();
      await fetchVectorstoreStatistics();
    };
    
    fetchData();
  }, []);

  const handleRefresh = async () => {
    await fetchDocuments();
    await fetchVectorstoreStatistics();
  };

  const formatTimestamp = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('it-IT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return timestamp || 'Data non disponibile';
    }
  };

  const getDocumentsToday = () => {
    const today = new Date().toDateString();
    return documents.filter(doc => {
      try {
        const docDate = new Date(doc.timestamp).toDateString();
        return docDate === today;
      } catch {
        return false;
      }
    });
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Elaborazione Documenti</h2>
        <p className="text-gray-600">Monitora l'avanzamento dell'elaborazione e vettorizzazione dei documenti</p>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow border">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Statistiche Elaborazione</h3>
          <button 
            onClick={handleRefresh}
            disabled={loading}
            className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 text-sm"
          >
            {loading ? 'Aggiornando...' : '🔄 Aggiorna'}
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            Errore: {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded">
            <h4 className="font-semibold text-blue-700">Documenti in Coda</h4>
            <p className="text-2xl font-bold text-blue-600">{loading ? '...' : vectorstoreStats.queue}</p>
            <p className="text-xs text-blue-500">Monitor PDF in elaborazione</p>
          </div>
          <div className="bg-green-50 p-4 rounded">
            <h4 className="font-semibold text-green-700">Elaborati Oggi</h4>
            <p className="text-2xl font-bold text-green-600">
              {loading ? '...' : vectorstoreStats.today}
            </p>
            <p className="text-xs text-green-500">Vettorizzati nelle ultime 24h</p>
          </div>
          <div className="bg-purple-50 p-4 rounded">
            <h4 className="font-semibold text-purple-700">Totale Elaborati</h4>
            <p className="text-2xl font-bold text-purple-600">
              {loading ? '...' : vectorstoreStats.total}
            </p>
            <p className="text-xs text-purple-500">Documenti nel vector store</p>
          </div>
        </div>
        
        <div className="mt-6">
          <h4 className="font-semibold mb-3">Ultimi Documenti Elaborati</h4>
          {loading ? (
            <div className="p-4 text-center">
              <p className="text-gray-500">Caricamento documenti...</p>
            </div>
          ) : error ? (
            <div className="p-4 text-center">
              <p className="text-red-500">Impossibile caricare l'elenco documenti</p>
            </div>
          ) : documents.length === 0 ? (
            <div className="p-4 text-center">
              <p className="text-gray-500">Nessun documento elaborato</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome File</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stato</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {documents.slice(0, 10).map((doc, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{doc.filename || 'Nome non disponibile'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatTimestamp(doc.timestamp)}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                          Completato
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Componente per la ricerca semantica
const SemanticSearch = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/database-management/vectorstore/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || 'fake-token'}`
        },
        body: JSON.stringify({ query: query.trim() })
      });
      
      if (!response.ok) {
        throw new Error(`Errore ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error('Errore durante la ricerca semantica:', error);
      alert('Errore durante la ricerca semantica');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Ricerca Semantica</h2>
        <p className="text-gray-600">Cerca informazioni nei documenti vettorizzati utilizzando l'AI</p>
      </div>

      {/* Area di ricerca */}
      <div className="bg-white p-6 rounded-lg shadow border mb-6">
        <div className="flex gap-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Inserisci la tua domanda sui documenti..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Cercando...' : 'Cerca'}
          </button>
        </div>
        
        <div className="mt-4 text-sm text-gray-500">
          <p>💡 <strong>Esempi di domande:</strong></p>
          <ul className="mt-2 space-y-1">
            <li>• "Riassumi il contenuto del documento"</li>
            <li>• "Trova informazioni sui requisiti di sistema"</li>
            <li>• "Quali sono i punti principali del contratto?"</li>
          </ul>
        </div>
      </div>

      {/* Risultati dal vectorstore */}
      {results.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Documenti più simili</h3>
          {results.map((result, idx) => (
            <div key={idx} className="bg-white p-6 rounded-lg shadow border">
              <div className="mb-2">
                <span className="text-xs text-gray-500">Score: {result.score !== undefined ? result.score : 'N/A'}</span>
              </div>
              <div className="mb-2">
                <span className="font-semibold text-gray-900">Estratto:</span>
                <p className="text-gray-700 bg-blue-50 p-3 rounded mt-1">{result.content}</p>
              </div>
              <div className="mb-2">
                <span className="font-semibold text-gray-900">Metadati:</span>
                <pre className="text-xs bg-gray-50 p-2 rounded mt-1">{JSON.stringify(result.metadata, null, 2)}</pre>
              </div>
            </div>
          ))}
        </div>
      )}

      {results.length === 0 && (
        <div className="bg-gray-50 p-8 rounded-lg text-center">
          <p className="text-gray-500">Nessuna ricerca effettuata. Inizia digitando una domanda sopra.</p>
        </div>
      )}
    </div>
  );
};

// Tab per visualizzare i documenti indicizzati nel vectorstore
const VectorstoreList = ({ activeTab }) => {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchVectorstoreDocs = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/database-management/vectorstore/documents`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || 'fake-token'}`
        }
      });
      const data = await response.json();
      setDocs(data.documents || []);
    } catch (err) {
      setError('Errore nel recupero dei documenti indicizzati');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'vectorstore') fetchVectorstoreDocs();
  }, [activeTab]);

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Documenti indicizzati nel Vectorstore</h2>
      {loading && <p>Caricamento...</p>}
      {error && <div className="bg-red-100 p-3 rounded mb-4">{error}</div>}
      {!loading && docs.length === 0 && <p>Nessun documento indicizzato.</p>}
      {!loading && docs.length > 0 && (
        <div className="space-y-4">
          {docs.map((doc, idx) => (
            <div key={doc.id || idx} className="bg-white p-4 rounded shadow border">
              <div className="mb-2 text-xs text-gray-500">ID: {doc.id}</div>
              <div className="mb-2">
                <span className="font-semibold">Metadati:</span>
                <pre className="bg-gray-50 p-2 rounded text-xs mt-1">{JSON.stringify(doc.metadata, null, 2)}</pre>
              </div>
              <div className="mb-2">
                <span className="font-semibold">Contenuto:</span>
                <div className="bg-blue-50 p-2 rounded text-sm mt-1">{doc.content}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Componente principale con tabs
const DocumentManagement = () => {
  const [activeTab, setActiveTab] = useState('monitoring');

  const tabs = [
    { id: 'monitoring', label: 'Monitoraggio', icon: '📊' },
    { id: 'processing', label: 'Elaborazione', icon: '⚙️' },
    { id: 'search', label: 'Ricerca Semantica', icon: '🔍' },
    { id: 'database', label: 'Database', icon: '🗄️' },
    { id: 'vectorstore', label: 'Documenti indicizzati', icon: '📄' },
    { id: 'vectorstoreSettings', label: 'Impostazioni Vectorstore', icon: '⚙️' }
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'monitoring':
        return <PDFMonitoringPanel />;
      case 'processing':
        return <DocumentProcessing />;
      case 'search':
        return <SemanticSearch />;
      case 'database':
        return <DatabaseManagementSimple />;
      case 'vectorstore':
        return <VectorstoreList activeTab={activeTab} />;
      case 'vectorstoreSettings':
        return <VectorstoreSettings />;
      default:
        return <PDFMonitoringPanel />;
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header con tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Gestione Documenti</h1>
          <div className="flex space-x-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-700 border border-blue-200'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Contenuto */}
      <div className="flex-1 overflow-auto">
        {renderContent()}
      </div>
    </div>
  );
};

export default DocumentManagement;
