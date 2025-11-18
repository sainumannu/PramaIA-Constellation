/**
 * Hook per ascoltare gli eventi di caricamento dei file da cartelle monitorate
 */
import { useEffect, useRef } from 'react';

// Intervallo di polling breve (in ms)
const POLLING_INTERVAL = 1000;

/**
 * Hook che rileva nuovi file caricati e scatena un callback
 * 
 * @param {Function} onFileUploaded - Callback da eseguire quando viene rilevato un nuovo file
 * @returns {Object} Un oggetto con metodi per controllare il listener
 */
const useFileUploadListener = (onFileUploaded) => {
  const lastCheckTimeRef = useRef(new Date().getTime());
  const intervalRef = useRef(null);
  const isActiveRef = useRef(false);

  // Funzione che controlla se ci sono stati nuovi upload
  const checkForNewUploads = async () => {
    if (!isActiveRef.current) return;
    
    try {
      // Seleziona un client PDF Monitor attivo (questa logica dovrebbe essere coordinata con il componente principale)
      const activeEndpoint = sessionStorage.getItem('activePdfMonitorEndpoint');
      if (!activeEndpoint) return;
      
      const currentTime = new Date().getTime();
      const response = await fetch(`${activeEndpoint}/monitor/events/recent?limit=5`);
      
      if (response.ok) {
        const data = await response.json();
        const recentEvents = data.events || [];
        
        // Verifica se ci sono eventi recenti (ultimi 5 secondi)
        const newEvents = recentEvents.filter(event => {
          const eventTime = new Date(event.timestamp).getTime();
          return eventTime > lastCheckTimeRef.current && eventTime <= currentTime;
        });
        
        if (newEvents.length > 0) {
          console.log(`[FileUploadListener] Rilevati ${newEvents.length} nuovi eventi`);
          // Chiama il callback con i nuovi eventi
          onFileUploaded(newEvents);
        }
        
        // Aggiorna l'ultimo timestamp di controllo
        lastCheckTimeRef.current = currentTime;
      }
    } catch (error) {
      console.error('[FileUploadListener] Errore durante il controllo di nuovi upload:', error);
    }
  };

  // Avvia l'ascolto
  const startListening = () => {
    if (!isActiveRef.current) {
      isActiveRef.current = true;
      intervalRef.current = setInterval(checkForNewUploads, POLLING_INTERVAL);
      console.log('[FileUploadListener] Ascolto avviato');
    }
  };

  // Ferma l'ascolto
  const stopListening = () => {
    if (isActiveRef.current) {
      isActiveRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      console.log('[FileUploadListener] Ascolto fermato');
    }
  };

  // Gestisce l'avvio e l'arresto dell'ascolto quando il componente viene montato/smontato
  useEffect(() => {
    startListening();
    
    // Cleanup quando il componente viene smontato
    return () => {
      stopListening();
    };
  }, []);

  return {
    startListening,
    stopListening,
    isListening: isActiveRef.current
  };
};

export default useFileUploadListener;
