import React from 'react';

function WorkflowsPage() {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Workflows</h1>
      <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4">
        <p className="font-bold">Informazione</p>
        <p>Questa è una pagina segnaposto per i Workflows. La funzionalità completa è stata temporaneamente disabilitata.</p>
      </div>
      
      <div className="bg-white shadow-md rounded p-4">
        <h2 className="text-xl font-semibold mb-2">Workflows Disponibili</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
          {/* Workflow Card 1 */}
          <div className="border rounded p-4 bg-white shadow-sm">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold text-lg">Analisi Fatture</h3>
              <span className="px-2 py-1 rounded bg-green-100 text-green-800 text-xs">Attivo</span>
            </div>
            <p className="text-gray-600 text-sm mt-2">Workflow per l'analisi automatica delle fatture in arrivo.</p>
            <div className="flex justify-between mt-4">
              <button className="text-blue-500 hover:underline text-sm">Modifica</button>
              <span className="text-xs text-gray-500">Ultima esecuzione: 15:30</span>
            </div>
          </div>
          
          {/* Workflow Card 2 */}
          <div className="border rounded p-4 bg-white shadow-sm">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold text-lg">Estrazione Dati</h3>
              <span className="px-2 py-1 rounded bg-green-100 text-green-800 text-xs">Attivo</span>
            </div>
            <p className="text-gray-600 text-sm mt-2">Estrae dati strutturati da documenti PDF non formattati.</p>
            <div className="flex justify-between mt-4">
              <button className="text-blue-500 hover:underline text-sm">Modifica</button>
              <span className="text-xs text-gray-500">Ultima esecuzione: 14:45</span>
            </div>
          </div>
          
          {/* Workflow Card 3 */}
          <div className="border rounded p-4 bg-white shadow-sm">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold text-lg">Notifiche Email</h3>
              <span className="px-2 py-1 rounded bg-red-100 text-red-800 text-xs">Inattivo</span>
            </div>
            <p className="text-gray-600 text-sm mt-2">Invia notifiche email quando vengono processati nuovi documenti.</p>
            <div className="flex justify-between mt-4">
              <button className="text-blue-500 hover:underline text-sm">Modifica</button>
              <span className="text-xs text-gray-500">Mai eseguito</span>
            </div>
          </div>
        </div>
        
        <div className="mt-8">
          <button className="bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 inline-flex items-center">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
            Crea Nuovo Workflow
          </button>
        </div>
      </div>
    </div>
  );
}

export default WorkflowsPage;
