/**
 * Hook personalizzato per gestire le sorgenti di eventi dinamiche
 * Sostituisce gli array hardcoded con chiamate API dinamiche
 */
import { useState, useEffect, useCallback } from 'react';
import { PDK_SERVER_BASE_URL } from '../config/appConfig';
import axios from 'axios';

export const useEventSources = () => {
  const [eventSources, setEventSources] = useState([]);
  const [eventTypes, setEventTypes] = useState([]);
  const [sourcesLoading, setSourcesLoading] = useState(true);
  const [sourcesError, setSourcesError] = useState(null);

  console.log('[useEventSources] Hook state update:', {
    eventSources: eventSources.length,
    eventTypes: eventTypes.length,
    sourcesLoading,
    sourcesError
  });

  // Carica tutte le sorgenti di eventi disponibili
  const loadEventSources = useCallback(async () => {
    try {
      setSourcesLoading(true);
      // Aggiungiamo timestamp per evitare cache
      const timestamp = new Date().getTime();
      console.log(`[useEventSources] Tentativo caricamento da: ${PDK_SERVER_BASE_URL}/api/event-sources`);
      
      // Chiama il server PDK invece del server principale
      const response = await axios.get(`${PDK_SERVER_BASE_URL}/api/event-sources?t=${timestamp}`, {
        timeout: 10000 // 10 secondi timeout
      });
      
      console.log('[useEventSources] Event sources response:', response.data);
      
      const sources = response.data || [];
      console.log(`[useEventSources] Loaded ${sources.length} event sources from PDK server`);
      setEventSources(sources);
      setSourcesError(null);
    } catch (err) {
      console.error('Errore nel caricamento delle sorgenti:', err.message, err.response?.status);
      
      // Messaggio di errore più specifico
      let errorMessage = 'Impossibile caricare le sorgenti di eventi';
      if (err.code === 'ECONNREFUSED' || err.message.includes('Network Error')) {
        errorMessage = 'PDK Server non raggiungibile. Verifica che sia avviato su porta 3001.';
      } else if (err.response?.status === 404) {
        errorMessage = 'Endpoint event sources non trovato sul PDK Server.';
      } else if (err.response?.status >= 500) {
        errorMessage = 'Errore interno del PDK Server.';
      }
      
      setSourcesError(errorMessage);
      
      // Fallback a sorgenti hardcoded per compatibilità
      const fallbackSources = [
        { 
          id: 'system', 
          name: 'Sistema (Fallback)', 
          description: 'Eventi interni del sistema - modalità fallback',
          eventTypes: [
            { id: 'system_event', name: 'Evento Sistema', description: 'Evento generico del sistema' }
          ]
        },
        { 
          id: 'api-webhook', 
          name: 'API Webhook (Fallback)', 
          description: 'Endpoint HTTP per eventi esterni - modalità fallback',
          eventTypes: [
            { id: 'webhook_received', name: 'Webhook Ricevuto', description: 'Webhook ricevuto dall\'esterno' }
          ]
        },
        {
          id: 'document-monitor',
          name: 'Document Monitor (Fallback)',
          description: 'Monitoring documenti - modalità fallback',
          eventTypes: [
            { id: 'document_uploaded', name: 'Documento Caricato', description: 'Nuovo documento caricato' },
            { id: 'pdf_processed', name: 'PDF Elaborato', description: 'PDF elaborato con successo' }
          ]
        }
      ];
      
      console.log('[useEventSources] Using fallback sources:', fallbackSources);
      setEventSources(fallbackSources);
    } finally {
      setSourcesLoading(false);
    }
  }, []);

  // Carica tutti i tipi di eventi disponibili
  const loadAllEventTypes = useCallback(async () => {
    console.log('[useEventSources] Loading all event types...');
    try {
      // Chiama il server PDK invece del server principale
      const response = await axios.get(`${PDK_SERVER_BASE_URL}/api/event-sources/events/all`, {
        timeout: 10000
      });
      console.log('[useEventSources] Event types response:', response.data);
      
      // Converte la struttura dei dati dal server alla struttura attesa dal componente
      const eventTypesData = response.data.eventTypes || response.data || [];
      const convertedEventTypes = eventTypesData.map(eventType => ({
        type: eventType.id || eventType.type,
        label: eventType.name || eventType.label,
        description: eventType.description,
        sourceId: eventType.sourceId,
        sourceName: eventType.sourceName
      }));
      
      console.log('[useEventSources] Converted event types:', convertedEventTypes);
      setEventTypes(convertedEventTypes);
    } catch (err) {
      console.error('Errore nel caricamento dei tipi di eventi:', err.message);
      // Fallback a tipi hardcoded più completi
      const fallbackEventTypes = [
        { 
          type: 'document_uploaded', 
          label: 'Upload Documento', 
          description: 'Quando un documento viene caricato nel sistema',
          sourceId: 'document-monitor',
          sourceName: 'Document Monitor'
        },
        { 
          type: 'pdf_processed', 
          label: 'PDF Elaborato', 
          description: 'Quando un PDF viene elaborato completamente',
          sourceId: 'document-monitor',
          sourceName: 'Document Monitor'
        },
        { 
          type: 'webhook_received', 
          label: 'Webhook Ricevuto', 
          description: 'Quando viene ricevuta una chiamata webhook',
          sourceId: 'api-webhook',
          sourceName: 'API Webhook'
        },
        { 
          type: 'system_event', 
          label: 'Evento Sistema', 
          description: 'Evento generico del sistema',
          sourceId: 'system',
          sourceName: 'Sistema'
        },
        {
          type: 'file_created',
          label: 'File Creato',
          description: 'Quando viene creato un nuovo file',
          sourceId: 'file-monitor',
          sourceName: 'File Monitor'
        },
        {
          type: 'database_change',
          label: 'Modifica Database',
          description: 'Quando viene modificato il database',
          sourceId: 'database-triggers',
          sourceName: 'Database Triggers'
        }
      ];
      
      console.log('[useEventSources] Using fallback event types:', fallbackEventTypes);
      setEventTypes(fallbackEventTypes);
    }
  }, []);

  // Carica tipi di eventi per una sorgente specifica
  const loadEventTypesForSource = useCallback(async (sourceId) => {
    try {
      // Aggiungiamo timestamp per evitare cache
      const timestamp = new Date().getTime();
      // Chiama il server PDK invece del server principale
      const response = await axios.get(`${PDK_SERVER_BASE_URL}/api/event-sources/${sourceId}/events?t=${timestamp}`);
      console.log(`[useEventSources] Events for ${sourceId}:`, response.data);
      
      const eventTypesData = response.data.eventTypes || response.data || [];
      
      // Converte la struttura dei dati dal server alla struttura attesa dal componente
      const convertedEventTypes = eventTypesData.map(eventType => ({
        type: eventType.id || eventType.type,
        label: eventType.name || eventType.label,
        description: eventType.description,
        sourceId: eventType.sourceId || sourceId,
        sourceName: eventType.sourceName
      }));
      
      console.log(`[useEventSources] Converted events for ${sourceId}:`, convertedEventTypes);
      return convertedEventTypes;
    } catch (err) {
      console.error(`Errore nel caricamento eventi per ${sourceId}:`, err);
      return [];
    }
  }, []);

  // Carica dettagli di una sorgente specifica
  const loadEventSource = useCallback(async (sourceId) => {
    try {
      // Chiama il server PDK invece del server principale
      const response = await axios.get(`${PDK_SERVER_BASE_URL}/api/event-sources/${sourceId}`);
      return response.data;
    } catch (err) {
      console.error(`Errore nel caricamento sorgente ${sourceId}:`, err);
      return null;
    }
  }, []);

  useEffect(() => {
    console.log('[useEventSources] Hook initialized, calling loadEventSources and loadAllEventTypes');
    loadEventSources();
    loadAllEventTypes();
  }, [loadEventSources, loadAllEventTypes]);

  return {
    eventSources,
    eventTypes,
    sourcesLoading,
    sourcesError,
    loadEventSources,
    loadAllEventTypes,
    loadEventTypesForSource,
    loadEventSource
  };
};

export default useEventSources;
