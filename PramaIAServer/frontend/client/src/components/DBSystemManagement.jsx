import React, { useState } from 'react';
import DocumentDBManagement from './DocumentDBManagement';
import VectorDBManagement from './VectorDBManagement';

const DBSystemManagement = () => {
  const [activeTab, setActiveTab] = useState('document');

  const tabs = [
    { id: 'document', label: 'Database Documenti', icon: '📄' },
    { id: 'vector', label: 'Vector Store', icon: '🔍' },
    { id: 'system', label: 'Sistema', icon: '⚙️' }
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'document':
        return <DocumentDBManagement />;
      case 'vector':
        return <VectorDBManagement />;
      case 'system':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold mb-4">Gestione Sistema Database</h2>
            <div className="bg-white p-6 rounded-lg shadow border">
              <h3 className="font-semibold text-lg mb-2">Informazioni di Sistema</h3>
              <p className="text-gray-600 mb-4">
                Questa sezione contiene informazioni generali sul sistema di database utilizzato nell'applicazione.
              </p>
              
              <div className="space-y-4">
                <div className="bg-blue-50 p-4 rounded">
                  <h4 className="font-semibold text-blue-700 mb-2">Database Documenti</h4>
                  <p className="text-gray-700">
                    Il database documenti è implementato utilizzando SQLite e memorizza i metadati dei documenti elaborati.
                    Contiene informazioni come nome del file, data di elaborazione, numero di pagine e altri metadati.
                  </p>
                </div>
                
                <div className="bg-green-50 p-4 rounded">
                  <h4 className="font-semibold text-green-700 mb-2">Vector Store</h4>
                  <p className="text-gray-700">
                    Il Vector Store è implementato utilizzando ChromaDB e memorizza i vettori di embedding dei documenti.
                    Permette di eseguire ricerche semantiche sui contenuti dei documenti elaborati.
                  </p>
                </div>
                
                <div className="bg-purple-50 p-4 rounded">
                  <h4 className="font-semibold text-purple-700 mb-2">Backup</h4>
                  <p className="text-gray-700">
                    I backup vengono archiviati nella directory 'backups' del server. È possibile creare backup
                    separati per il database documenti e per il vector store dalle rispettive schede.
                  </p>
                </div>
              </div>
            </div>
          </div>
        );
      default:
        return <DocumentDBManagement />;
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Tabs di navigazione */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Gestione Database</h1>
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

export default DBSystemManagement;
