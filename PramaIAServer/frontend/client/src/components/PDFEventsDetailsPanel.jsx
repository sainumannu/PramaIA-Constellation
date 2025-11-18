import React from 'react';
import { API_URLS } from '../utils/apiUtils';

const PDFEventsDetailsPanel = ({
  pdfEvents,
  fetchPdfEvents,
  loadClients
}) => {

  return (
    <div className="bg-white p-6 rounded-lg shadow border mb-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-semibold">� Statistiche e Analisi Eventi PDF</h3>
        <div className="flex space-x-2">
          <button 
            onClick={fetchPdfEvents}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Aggiorna
          </button>
        </div>
      </div>
      
      <div className="mb-4 bg-blue-50 p-3 rounded">
        <p className="text-sm flex items-center">
          <span className="mr-1">ℹ️</span>
          <span>
            <strong>Informazioni:</strong> In questa scheda sono visualizzate statistiche avanzate e analisi dettagliate degli eventi documento.
            La gestione degli eventi recenti e la pulizia sono disponibili nella scheda "Attività Recenti".
          </span>
        </p>
      </div>

      <div>
        {!pdfEvents ? (
          <p>Caricamento eventi PDF...</p>
        ) : pdfEvents.error ? (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            Errore: {pdfEvents.error}
          </div>
        ) : (
          <div>
            <div className="mb-4 p-3 bg-purple-50 rounded">
              <p className="font-semibold">Totale eventi PDF: {pdfEvents.total}</p>
              <p className="text-sm text-gray-600">{pdfEvents.message}</p>
            </div>

            {/* Statistiche per file */}
            {pdfEvents.file_statistics && pdfEvents.file_statistics.length > 0 && (
              <div className="mb-4">
                <h4 className="font-semibold mb-2">📊 Statistiche per File</h4>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {pdfEvents.file_statistics.map((stat, index) => (
                    <div key={index} className="border p-2 rounded bg-gray-50">
                      <div className="flex justify-between items-center">
                        <span className="font-medium">{stat.file_name || 'File sconosciuto'}</span>
                        <div className="flex gap-2 text-sm">
                          <span className="bg-blue-100 px-2 py-1 rounded">
                            {stat.event_count} eventi
                          </span>
                          <span className="bg-green-100 px-2 py-1 rounded">
                            {stat.unique_document_ids} doc IDs
                          </span>
                        </div>
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        Stati: {stat.statuses.join(', ')}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Lista eventi dettagliata */}
            {pdfEvents.events && pdfEvents.events.length > 0 ? (
              <div>
                <h4 className="font-semibold mb-2">📋 Ultimi Eventi (max 100)</h4>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {pdfEvents.events.map((event, index) => (
                    <div key={index} className="border p-3 rounded bg-gray-50">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
                        <div>
                          <strong>File:</strong> {event.file_name || 'N/A'}
                        </div>
                        <div>
                          <strong>Status:</strong> 
                          <span className={`ml-1 px-2 py-1 rounded text-xs ${
                            event.status === 'completed' ? 'bg-green-100 text-green-800' :
                            event.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                            event.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {event.status}
                          </span>
                        </div>
                        <div>
                          <strong>Tipo:</strong> {event.event_type}
                        </div>
                        <div>
                          <strong>Timestamp:</strong> {new Date(event.timestamp).toLocaleString()}
                        </div>
                        <div>
                          <strong>Document ID:</strong> 
                          <span className="font-mono text-xs bg-gray-200 px-1 rounded ml-1">
                            {event.document_id ? event.document_id.substring(0, 15) + '...' : 'N/A'}
                          </span>
                        </div>
                        <div>
                          <strong>ID Evento:</strong> {event.id}
                        </div>
                      </div>
                      {event.file_path && (
                        <div className="mt-2 text-xs">
                          <strong>Path:</strong> 
                          <span className="bg-gray-200 px-1 rounded ml-1 font-mono">
                            {event.file_path}
                          </span>
                        </div>
                      )}
                      {event.metadata && (
                        <div className="mt-2 text-xs">
                          <strong>Metadata:</strong>
                          <div className="bg-white p-1 rounded mt-1 max-h-16 overflow-y-auto font-mono">
                            {event.metadata}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-gray-500">Nessun evento PDF trovato</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PDFEventsDetailsPanel;
