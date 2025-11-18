import React, { useState } from 'react';
import { deleteEvent, retryEvent, clearAllEvents } from '../api/monitoring';
import { API_URLS, createFetchConfig } from '../utils/apiUtils';

const EventsPanel = ({
  clients,
  recentEvents,
  filteredEvents,
  loadingEvents,
  selectedEndpoint,
  setSelectedEndpoint,
  eventsPerPage,
  setEventsPerPage,
  currentPage,
  setCurrentPage,
  loadRecentEvents,
  processingEventId,
  setProcessingEventId,
  currentEvents,
  totalPages
}) => {
  // Configurazione di retention degli eventi
  const PDF_EVENTS_MAX_AGE_HOURS = 24;  // Mantieni solo gli eventi delle ultime 24 ore
  const PDF_EVENTS_MAX_COUNT = 1000;     // Mantieni massimo 1000 eventi
  
  // Stato per la pulizia automatica
  const [cleanupLoading, setCleanupLoading] = useState(false);
  const [cleanupResults, setCleanupResults] = useState(null);
  
  // Funzione per eseguire la pulizia automatica
  const handleCleanupEvents = async () => {
    if (!window.confirm(`Sei sicuro di voler eseguire la pulizia automatica degli eventi?\nSaranno mantenuti solo gli eventi delle ultime ${PDF_EVENTS_MAX_AGE_HOURS} ore, fino a un massimo di ${PDF_EVENTS_MAX_COUNT} eventi.`)) {
      return;
    }

    setCleanupLoading(true);
    setCleanupResults(null);
    
    try {
      const response = await fetch(
        `${API_URLS.DATABASE_MANAGEMENT}/pdf-events/cleanup?max_age_hours=${PDF_EVENTS_MAX_AGE_HOURS}&max_events=${PDF_EVENTS_MAX_COUNT}`, 
        createFetchConfig('POST')
      );
      
      const data = await response.json();
      setCleanupResults(data);
      
      if (data.success) {
        // Aggiorna i dati dopo la pulizia
        loadRecentEvents();
      }
    } catch (e) {
      console.error('Errore durante la pulizia degli eventi:', e);
      setCleanupResults({ 
        success: false, 
        message: `Errore: ${e.message}` 
      });
    } finally {
      setCleanupLoading(false);
    }
  };

  // Handler per eliminare un evento
  const handleDeleteEvent = async (event) => {
    if (!window.confirm(`Sei sicuro di voler eliminare l'evento per il file "${event.file_name}"?`)) {
      return;
    }
    
    // Trova il client attivo
    const activeClient = clients.find(c => c.status !== 'offline');
    if (!activeClient) {
      alert("Nessun client PDF Monitor attivo");
      return;
    }
    
    try {
      setProcessingEventId(event.id);
      const result = await deleteEvent(activeClient, event.id);
      if (result.status === "success") {
        alert("Evento eliminato con successo");
        // Ricarica gli eventi
        loadRecentEvents();
      } else {
        alert(`Errore: ${result.message || "Operazione fallita"}`);
      }
    } catch (e) {
      alert(`Errore durante l'eliminazione: ${e.message}`);
      console.error("Errore eliminazione evento:", e);
    } finally {
      setProcessingEventId(null);
    }
  };
  
  // Handler per riprovare un evento
  const handleRetryEvent = async (event) => {
    // Trova il client attivo
    const activeClient = clients.find(c => c.status !== 'offline');
    if (!activeClient) {
      alert("Nessun client PDF Monitor attivo");
      return;
    }
    
    try {
      setProcessingEventId(event.id);
      const result = await retryEvent(activeClient, event.id);
      if (result.status === "success") {
        alert("Rielaborazione avviata con successo");
        // Ricarica gli eventi
        loadRecentEvents();
      } else {
        alert(`Errore: ${result.message || "Operazione fallita"}`);
      }
    } catch (e) {
      alert(`Errore durante la rielaborazione: ${e.message}`);
      console.error("Errore rielaborazione evento:", e);
    } finally {
      setProcessingEventId(null);
    }
  };
  
  // Paginazione
  const paginate = (pageNumber) => setCurrentPage(pageNumber);
  
  // Calcolo degli indici per paginazione
  const indexOfLastEvent = currentPage * eventsPerPage;
  const indexOfFirstEvent = indexOfLastEvent - eventsPerPage;

  return (
    <div>
      {/* Politica di retention */}
      <div className="mb-4 bg-blue-50 p-3 rounded">
        <p className="text-sm flex items-center">
          <span className="mr-1">⚙️</span>
          <span>
            <strong>Politica di retention:</strong> Gli eventi vengono mantenuti per massimo {PDF_EVENTS_MAX_AGE_HOURS} ore, 
            fino a un massimo di {PDF_EVENTS_MAX_COUNT} eventi. I record più vecchi vengono eliminati automaticamente.
          </span>
        </p>
      </div>
      
      {/* Risultati pulizia automatica */}
      {cleanupResults && (
        <div className={`mb-4 p-3 rounded ${cleanupResults.success ? 'bg-green-50' : 'bg-red-50'}`}>
          <p className={`text-sm ${cleanupResults.success ? 'text-green-700' : 'text-red-700'}`}>
            {cleanupResults.message}
          </p>
          {cleanupResults.success && cleanupResults.details && (
            <div className="mt-2 text-xs">
              <p>Eventi iniziali: <strong>{cleanupResults.details.initial_count}</strong></p>
              <p>Eventi eliminati per età: <strong>{cleanupResults.details.deleted_by_age}</strong></p>
              <p>Eventi eliminati per limite massimo: <strong>{cleanupResults.details.deleted_by_count}</strong></p>
              <p>Eventi rimanenti: <strong>{cleanupResults.details.final_count}</strong></p>
            </div>
          )}
        </div>
      )}
      
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-blue-700">Attività Recenti</h2>
        <div className="flex items-center gap-4">
          <div className="flex items-center">
            <label htmlFor="endpoint-filter" className="mr-2 text-sm text-gray-600">Filtra per endpoint:</label>
            <select 
              id="endpoint-filter"
              className="text-sm border rounded px-2 py-1"
              value={selectedEndpoint}
              onChange={(e) => setSelectedEndpoint(e.target.value)}
            >
              <option value="all">Tutti gli endpoint</option>
              {clients.map(client => (
                <option key={client.id} value={client.endpoint}>{client.name}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center">
            <label htmlFor="items-per-page" className="mr-2 text-sm text-gray-600">Righe per pagina:</label>
            <select 
              id="items-per-page"
              className="text-sm border rounded px-2 py-1"
              value={eventsPerPage}
              onChange={(e) => {
                setEventsPerPage(Number(e.target.value));
                setCurrentPage(1); // Torna alla prima pagina
              }}
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
          <button
            onClick={handleCleanupEvents}
            disabled={cleanupLoading}
            className="px-3 py-1 rounded bg-yellow-100 text-yellow-700 hover:bg-yellow-200 text-xs ml-2 disabled:opacity-50"
            title="Pulizia automatica degli eventi secondo la politica di retention"
          >
            {cleanupLoading ? 'Pulizia...' : '🧹 Pulizia Automatica'}
          </button>
          <button 
            className="px-3 py-1 rounded bg-gray-100 text-gray-700 hover:bg-gray-200 text-xs"
            onClick={loadRecentEvents}
            disabled={loadingEvents}
          >
            {loadingEvents ? "Aggiornamento..." : "↻ Aggiorna"}
          </button>
          <button
            className="px-3 py-1 rounded bg-red-100 text-red-700 hover:bg-red-200 text-xs ml-2"
            onClick={async () => {
              if (!window.confirm(selectedEndpoint === 'all'
                ? 'Sei sicuro di voler eliminare TUTTI gli eventi recenti da tutti gli endpoint?'
                : 'Sei sicuro di voler eliminare tutti gli eventi recenti per questo endpoint?')) return;
              let success = true;
              if (selectedEndpoint === 'all') {
                for (const client of clients.filter(c => c.status !== 'offline')) {
                  const result = await clearAllEvents(client);
                  if (result.status !== 'success') success = false;
                }
              } else {
                const client = clients.find(c => c.endpoint === selectedEndpoint);
                if (client) {
                  const result = await clearAllEvents(client);
                  if (result.status !== 'success') success = false;
                }
              }
              if (success) {
                alert('Eventi eliminati con successo');
              } else {
                alert('Errore durante la rimozione di uno o più eventi');
              }
              loadRecentEvents();
            }}
            disabled={loadingEvents || clients.length === 0}
            title="Elimina tutti gli eventi recenti"
          >
            🗑️ Ripulisci tutti
          </button>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm border">
          <thead>
            <tr className="bg-gray-100">
              <th className="px-2 py-1">Timestamp</th>
              <th className="px-2 py-1">File</th>
              <th className="px-2 py-1">Cartella</th>
              <th className="px-2 py-1">Evento</th>
              <th className="px-2 py-1">Stato</th>
              <th className="px-2 py-1 w-40">Document ID</th>
              <th className="px-2 py-1 w-24">Azioni</th>
            </tr>
          </thead>
          <tbody>
            {loadingEvents && currentEvents.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-4">Caricamento eventi...</td></tr>
            ) : currentEvents.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-4">Nessun evento recente{selectedEndpoint !== 'all' ? ' per questo endpoint' : ''}</td></tr>
            ) : (
              currentEvents.map(event => (
                <tr key={event.id} className="border-b hover:bg-gray-50">
                  <td className="px-2 py-1 text-xs text-gray-500">
                    {new Date(event.timestamp).toLocaleString()}
                  </td>
                  <td className="px-2 py-1 font-medium">{event.file_name}</td>
                  <td className="px-2 py-1 text-xs">{event.folder}</td>
                  <td className="px-2 py-1 flex items-center">
                    {event.event_type === 'created' ? (
                      <span className="px-1.5 py-0.5 rounded-full bg-green-100 text-green-800 text-xs">Aggiunto</span>
                    ) : event.event_type === 'deleted' ? (
                      <span className="px-1.5 py-0.5 rounded-full bg-red-100 text-red-800 text-xs">Rimosso</span>
                    ) : event.event_type === 'renamed' ? (
                      <span className="px-1.5 py-0.5 rounded-full bg-yellow-100 text-yellow-800 text-xs">Rinominato</span>
                    ) : (
                      <span className="px-1.5 py-0.5 rounded-full bg-blue-100 text-blue-800 text-xs">{event.event_type}</span>
                    )}
                    {/* Tooltip/lente per eventi moved/path_changed/renamed */}
                    {(event.event_type === 'moved' || event.event_type === 'path_changed' || event.event_type === 'renamed') && event.error_message && (() => {
                      try {
                        const moveInfo = JSON.parse(event.error_message);
                        return (
                          <span className="relative group ml-2">
                            <span className="inline-block cursor-pointer text-blue-600" title={event.event_type === 'renamed' ? "Dettagli rinomina" : "Dettagli spostamento"}>
                              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M11 6a5 5 0 1 0-2.236 4.19l3.387 3.387a1 1 0 0 0 1.415-1.415l-3.387-3.387A4.978 4.978 0 0 0 11 6zm-5 3a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/></svg>
                            </span>
                            <span className="absolute left-6 top-0 z-10 hidden group-hover:block bg-white border border-gray-300 rounded shadow-lg p-2 text-xs min-w-[180px]">
                              {event.event_type === 'renamed' ? (
                                moveInfo.details ? 
                                <div className="font-semibold">{moveInfo.details}</div> : 
                                <><b>Rinominato da:</b> <span className="font-medium">{moveInfo.old_name}</span><br/><b>a:</b> <span className="font-medium">{moveInfo.new_name}</span></>
                              ) : (
                                <><b>Spostato da:</b><br/>{moveInfo.from}<br/><b>a:</b><br/>{moveInfo.to}</>
                              )}
                            </span>
                          </span>
                        );
                      } catch (e) { return null; }
                    })()}
                  </td>
                  <td className="px-2 py-1">
                    {event.status === 'pending' && (
                      <span className="px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-800 text-xs">In attesa</span>
                    )}
                    {event.status === 'processing' && (
                      <span className="px-1.5 py-0.5 rounded-full bg-yellow-100 text-yellow-800 text-xs">In elaborazione</span>
                    )}
                    {event.status === 'completed' && (
                      <span className="px-1.5 py-0.5 rounded-full bg-green-100 text-green-800 text-xs">Completato</span>
                    )}
                    {event.status === 'error' && (
                      <span className="px-1.5 py-0.5 rounded-full bg-red-100 text-red-800 text-xs" title={event.error_message || 'Errore sconosciuto'}>
                        Errore
                      </span>
                    )}
                  </td>
                  <td className="px-2 py-1 font-mono text-xs">
                    {event.document_id ? (
                      <div className="flex items-center gap-1">
                        <span className="text-blue-600 bg-blue-50 p-1 rounded overflow-x-auto whitespace-nowrap max-w-[150px]" title={event.document_id}>
                          {event.document_id}
                        </span>
                        <button 
                          className="text-gray-400 hover:text-gray-600 flex-shrink-0" 
                          onClick={() => {
                            navigator.clipboard.writeText(event.document_id);
                            alert('ID copiato negli appunti');
                          }}
                          title="Copia ID"
                        >
                          📋
                        </button>
                      </div>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-2 py-1 flex gap-1">
                    {event.status === 'error' && (
                      <button 
                        className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 hover:bg-blue-200 text-xs"
                        onClick={() => handleRetryEvent(event)}
                        disabled={processingEventId === event.id}
                        title="Riprova elaborazione"
                      >
                        {processingEventId === event.id ? "..." : "↻ Riprova"}
                      </button>
                    )}
                    <button 
                      className="px-1.5 py-0.5 rounded bg-red-100 text-red-700 hover:bg-red-200 text-xs"
                      onClick={() => handleDeleteEvent(event)}
                      disabled={processingEventId === event.id}
                      title="Elimina evento"
                    >
                      {processingEventId === event.id ? "..." : "🗑️ Elimina"}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        
        {/* Paginazione */}
        {filteredEvents.length > 0 && (
          <div className="flex justify-between items-center mt-4">
            <div className="text-sm text-gray-600">
              Mostrando {indexOfFirstEvent + 1}-{Math.min(indexOfLastEvent, filteredEvents.length)} di {filteredEvents.length} eventi
            </div>
            <div className="flex gap-1">
              <button 
                className={`px-2 py-1 rounded ${currentPage === 1 ? 'bg-gray-100 text-gray-400' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'}`}
                onClick={() => paginate(1)}
                disabled={currentPage === 1}
              >
                «
              </button>
              <button 
                className={`px-2 py-1 rounded ${currentPage === 1 ? 'bg-gray-100 text-gray-400' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'}`}
                onClick={() => paginate(currentPage - 1)}
                disabled={currentPage === 1}
              >
                ‹
              </button>
              
              {/* Visualizzazione pagine */}
              <div className="flex">
                {[...Array(Math.min(5, totalPages))].map((_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }
                  
                  return (
                    <button 
                      key={i}
                      className={`px-3 py-1 rounded ${currentPage === pageNum ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'}`}
                      onClick={() => paginate(pageNum)}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>
              
              <button 
                className={`px-2 py-1 rounded ${currentPage === totalPages ? 'bg-gray-100 text-gray-400' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'}`}
                onClick={() => paginate(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                ›
              </button>
              <button 
                className={`px-2 py-1 rounded ${currentPage === totalPages ? 'bg-gray-100 text-gray-400' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'}`}
                onClick={() => paginate(totalPages)}
                disabled={currentPage === totalPages}
              >
                »
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EventsPanel;
