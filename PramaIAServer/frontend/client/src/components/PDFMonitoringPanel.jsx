import React, { useEffect, useState } from 'react';
import {
  fetchDocumentMonitorClients,
  fetchRecentEvents
} from '../api/monitoring';
import SyncMonitoringPanel from './SyncMonitoringPanel';
import ReconciliationTab from './ReconciliationTab';
import ClientsPanel from './ClientsPanel';
import EventsPanel from './EventsPanel';
import PDFEventsDetailsPanel from './PDFEventsDetailsPanel';
import { API_URLS, createFetchConfig } from '../utils/apiUtils';

const DocumentMonitoringPanel = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [recentEvents, setRecentEvents] = useState([]);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [selectedEndpoint, setSelectedEndpoint] = useState('all');
  const [filteredEvents, setFilteredEvents] = useState([]);
  const [activeTab, setActiveTab] = useState('clients'); // 'clients' | 'events' | 'sync' | 'pdfEventsDetails' | 'reconciliation'
  const [selectedClient, setSelectedClient] = useState(null);
  
  // Stati per la gestione dei dettagli PDF Monitor
  const [pdfEvents, setPdfEvents] = useState(null);
  const [cleanupLoading, setCleanupLoading] = useState(false);
  const [cleanupResults, setCleanupResults] = useState(null);
  
  // Configurazione di retention degli eventi PDF
  const PDF_EVENTS_MAX_AGE_HOURS = 24;  // Mantieni solo gli eventi delle ultime 24 ore
  const PDF_EVENTS_MAX_COUNT = 1000;     // Mantieni massimo 1000 eventi
  
  // Stato per la paginazione
  const [currentPage, setCurrentPage] = useState(1);
  const [eventsPerPage, setEventsPerPage] = useState(10);
  const [processingEventId, setProcessingEventId] = useState(null);
  
  // Eventi paginati
  const indexOfLastEvent = currentPage * eventsPerPage;
  const indexOfFirstEvent = indexOfLastEvent - eventsPerPage;
  const currentEvents = filteredEvents.slice(indexOfFirstEvent, indexOfLastEvent);
  const totalPages = Math.ceil(filteredEvents.length / eventsPerPage);

  const fetchPdfEvents = async () => {
    try {
      const response = await fetch(
        `${API_URLS.DATABASE_MANAGEMENT}/pdf-events/details`, 
        createFetchConfig()
      );
      const data = await response.json();
      setPdfEvents(data);
    } catch (error) {
      console.error('Errore nel recuperare eventi PDF:', error);
      setPdfEvents({ error: error.message });
    }
  };

  const loadClients = () => {
    setLoading(true);
    fetchDocumentMonitorClients()
      .then((clientsData) => {
        setClients(clientsData);
        // Se non c'è già un client selezionato, seleziona il primo client online
        if (!selectedClient) {
          const onlineClient = clientsData.find(c => c.status !== 'offline');
          if (onlineClient) {
            setSelectedClient(onlineClient);
          }
        } else {
          // Aggiorna il client selezionato con dati freschi
          const updatedSelectedClient = clientsData.find(c => c.id === selectedClient.id);
          if (updatedSelectedClient) {
            setSelectedClient(updatedSelectedClient);
          }
        }
      })
      .catch(e => setError('Errore nel caricamento dei client PDF monitor'))
      .finally(() => setLoading(false));
  };
  
  const loadRecentEvents = async () => {
    if (clients.length === 0) return;
    
    // Utilizza il primo client attivo per ottenere gli eventi
    const activeClient = clients.find(c => c.status !== 'offline');
    if (!activeClient) return;
    
    setLoadingEvents(true);
    try {
      const events = await fetchRecentEvents(activeClient, 100); // Richiedi fino a 100 eventi
      setRecentEvents(events);
      // Applicare il filtro corrente dopo aver caricato i nuovi eventi
      applyEndpointFilter(events, selectedEndpoint);
      // Resetta la paginazione alla prima pagina
      setCurrentPage(1);
    } catch (e) {
      console.error("Errore caricamento eventi recenti:", e);
    } finally {
      setLoadingEvents(false);
    }
  };
  
  // Funzione per filtrare gli eventi in base all'endpoint selezionato
  const applyEndpointFilter = (events = recentEvents, endpoint = selectedEndpoint) => {
    if (endpoint === 'all') {
      setFilteredEvents(events);
    } else {
      setFilteredEvents(events.filter(event => {
        // Trova il client che corrisponde alla cartella dell'evento
        const clientMatch = clients.find(client => 
          client.folders && client.folders.some(folder => 
            event.folder.startsWith(folder) || folder.startsWith(event.folder)
          )
        );
        return clientMatch && clientMatch.endpoint === endpoint;
      }));
    }
  };

  // Handler per la selezione del client
  const handleSelectClient = (client) => {
    setSelectedClient(client);
  };

  useEffect(() => {
    loadClients();
    
    // Imposta un intervallo per ricaricare i client ogni 30 secondi
    const interval = setInterval(loadClients, 30000);
    return () => clearInterval(interval);
  }, []);
  
  // Carica gli eventi recenti quando i client sono disponibili o cambiano
  useEffect(() => {
    if (clients.length > 0) {
      loadRecentEvents();
      
      // Imposta un intervallo per ricaricare gli eventi ogni 10 secondi
      const eventsInterval = setInterval(loadRecentEvents, 10000);
      return () => clearInterval(eventsInterval);
    }
  }, [clients]);
  
  // Aggiorna gli eventi filtrati quando cambia l'endpoint selezionato
  useEffect(() => {
    applyEndpointFilter();
  }, [selectedEndpoint, recentEvents]);

  return (
    <div className="p-6 bg-white rounded shadow max-w-5xl mx-auto space-y-8">
      {/* Tab di navigazione */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex">
          <button
            className={`py-2 px-4 border-b-2 font-medium text-sm ${
              activeTab === 'clients'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('clients')}
          >
            Client PDF Monitor
          </button>
          <button
            className={`py-2 px-4 border-b-2 font-medium text-sm ${
              activeTab === 'events'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('events')}
          >
            Attività Recenti
          </button>
          <button
            className={`py-2 px-4 border-b-2 font-medium text-sm ${
              activeTab === 'pdfEventsDetails'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => {
              setActiveTab('pdfEventsDetails');
              // Carica i dettagli degli eventi PDF se non sono già stati caricati
              if (!pdfEvents) {
                fetchPdfEvents();
              }
            }}
          >
            Dettagli Eventi PDF
          </button>
          <button
            className={`py-2 px-4 border-b-2 font-medium text-sm ${
              activeTab === 'sync'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('sync')}
          >
            Sincronizzazione
          </button>
          <button
            className={`py-2 px-4 border-b-2 font-medium text-sm ${
              activeTab === 'reconciliation'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('reconciliation')}
          >
            Riconciliazione
          </button>
        </nav>
      </div>
      
      {/* Contenuto del tab selezionato */}
      {activeTab === 'clients' && (
        <ClientsPanel 
          clients={clients} 
          loading={loading} 
          error={error} 
          selectedClient={selectedClient} 
          handleSelectClient={handleSelectClient} 
          loadClients={loadClients}
        />
      )}
      
      {activeTab === 'events' && (
        <EventsPanel 
          clients={clients}
          recentEvents={recentEvents}
          filteredEvents={filteredEvents}
          loadingEvents={loadingEvents}
          selectedEndpoint={selectedEndpoint}
          setSelectedEndpoint={setSelectedEndpoint}
          eventsPerPage={eventsPerPage}
          setEventsPerPage={setEventsPerPage}
          currentPage={currentPage}
          setCurrentPage={setCurrentPage}
          loadRecentEvents={loadRecentEvents}
          processingEventId={processingEventId}
          setProcessingEventId={setProcessingEventId}
          currentEvents={currentEvents}
          totalPages={totalPages}
        />
      )}
      
      {/* Tab Dettagli Eventi PDF Monitor */}
      {activeTab === 'pdfEventsDetails' && (
        <PDFEventsDetailsPanel 
          pdfEvents={pdfEvents}
          fetchPdfEvents={fetchPdfEvents}
          cleanupLoading={cleanupLoading}
          setCleanupLoading={setCleanupLoading}
          cleanupResults={cleanupResults}
          setCleanupResults={setCleanupResults}
          PDF_EVENTS_MAX_AGE_HOURS={PDF_EVENTS_MAX_AGE_HOURS}
          PDF_EVENTS_MAX_COUNT={PDF_EVENTS_MAX_COUNT}
          loadClients={loadClients}
        />
      )}
      
      {activeTab === 'sync' && (
        <SyncMonitoringPanel 
          clients={clients} 
          selectedClient={selectedClient}
        />
      )}
      
      {activeTab === 'reconciliation' && (
        <ReconciliationTab />
      )}
    </div>
  );
};

export default DocumentMonitoringPanel;
