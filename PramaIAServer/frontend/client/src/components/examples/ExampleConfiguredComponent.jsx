/**
 * Esempio di componente che utilizza la configurazione centralizzata
 * Questo file mostra le best practices per utilizzare la configurazione
 */

import React, { useState, useEffect } from 'react';
import { API_URLS, createFetchConfig, buildBackendApiUrl } from '../utils/apiUtils';
import { BACKEND_BASE_URL, PDK_SERVER_BASE_URL } from '../config/appConfig';

const ExampleConfiguredComponent = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // ✅ Metodo raccomandato: Usa le utility API
  const fetchDataWithUtils = async () => {
    setLoading(true);
    try {
      // Usa URL predefiniti
      const response = await fetch(API_URLS.DOCUMENTS, createFetchConfig());
      const data = await response.json();
      setData(data);
    } catch (error) {
      console.error('Errore:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // ✅ Alternativa: Costruisci URL dinamicamente
  const fetchCustomEndpoint = async (endpoint) => {
    try {
      const url = buildBackendApiUrl(endpoint);
      const response = await fetch(url, createFetchConfig());
      return await response.json();
    } catch (error) {
      console.error('Errore:', error);
      return null;
    }
  };
  
  // ✅ Per chiamate POST con dati
  const saveDocument = async (documentData) => {
    try {
      const response = await fetch(
        API_URLS.DOCUMENTS,
        createFetchConfig('POST', documentData)
      );
      return await response.json();
    } catch (error) {
      console.error('Errore salvataggio:', error);
      return null;
    }
  };
  
  // ✅ Per chiamate a servizi esterni (PDK)
  const fetchPDKData = async () => {
    try {
      const response = await fetch(API_URLS.PDK_PLUGINS, createFetchConfig());
      return await response.json();
    } catch (error) {
      console.error('Errore PDK:', error);
      return null;
    }
  };
  
  // ❌ NON FARE: URL hardcoded
  const badExample = async () => {
    // SBAGLIATO - non usare mai URL hardcoded
    // const response = await fetch('http://localhost:8000/api/documents/');
  };
  
  useEffect(() => {
    fetchDataWithUtils();
  }, []);
  
  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Esempio Configurazione Centralizzata</h2>
      
      <div className="mb-4">
        <h3 className="font-semibold">Informazioni Configurazione:</h3>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li><strong>Backend URL:</strong> {BACKEND_BASE_URL}</li>
          <li><strong>PDK Server URL:</strong> {PDK_SERVER_BASE_URL}</li>
          <li><strong>API Documents:</strong> {API_URLS.DOCUMENTS}</li>
          <li><strong>API Users:</strong> {API_URLS.USERS}</li>
        </ul>
      </div>
      
      <div className="space-y-2">
        <button 
          onClick={fetchDataWithUtils}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {loading ? 'Caricando...' : 'Carica Documenti'}
        </button>
        
        <button 
          onClick={() => fetchCustomEndpoint('api/custom/endpoint')}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 ml-2"
        >
          Endpoint Personalizzato
        </button>
        
        <button 
          onClick={fetchPDKData}
          className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 ml-2"
        >
          Carica Plugin PDK
        </button>
      </div>
      
      {data && (
        <div className="mt-4 p-4 bg-gray-100 rounded">
          <h4 className="font-semibold">Dati caricati:</h4>
          <pre className="text-xs mt-2 overflow-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default ExampleConfiguredComponent;
