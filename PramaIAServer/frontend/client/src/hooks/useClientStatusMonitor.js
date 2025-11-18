/**
 * Hook per il monitoraggio attivo dello stato dei client PDF Monitor
 */
import { useEffect, useRef } from 'react';

// Intervallo di polling rapido per i client (in ms)
const CLIENT_POLLING_INTERVAL = 2000;

/**
 * Hook che monitora attivamente lo stato dei client PDF Monitor
 * 
 * @param {Array} clients - Array dei client da monitorare
 * @param {Function} onClientStatusChange - Callback da eseguire quando cambia lo stato di un client
 * @returns {Object} Oggetto con metodi per controllare il monitoraggio
 */
const useClientStatusMonitor = (clients, onClientStatusChange) => {
  const intervalRef = useRef(null);
  const isActiveRef = useRef(false);
  const clientsRef = useRef(clients);

  // Aggiorna il riferimento ai client quando cambiano
  useEffect(() => {
    clientsRef.current = clients;
  }, [clients]);

  // Funzione che verifica lo stato dei client
  const checkClientStatus = async () => {
    if (!isActiveRef.current || !clientsRef.current || clientsRef.current.length === 0) return;
    
    try {
      // Controlla lo stato di ogni client in parallelo
      const statusChecks = clientsRef.current.map(async (client) => {
        try {
          const statusResp = await fetch(`${client.endpoint}/monitor/status`, {
            // Aggiungiamo un timeout breve per evitare di bloccare se un client non risponde
            signal: AbortSignal.timeout(1500)
          });
          
          if (!statusResp.ok) return { id: client.id, status: 'offline' };
          
          const status = await statusResp.json();
          return {
            id: client.id,
            status: status.is_running ? 'online' : 'paused',
            folders: status.monitoring_folders || [],
            autostart_folders: status.autostart_folders || []
          };
        } catch (e) {
          return { id: client.id, status: 'offline' };
        }
      });
      
      // Attendi tutti i controlli di stato
      const results = await Promise.all(statusChecks);
      
      // Filtra solo i client che hanno cambiato stato
      const changedClients = results.filter(result => {
        const client = clientsRef.current.find(c => c.id === result.id);
        return client && client.status !== result.status;
      });
      
      if (changedClients.length > 0) {
        console.log(`[ClientStatusMonitor] ${changedClients.length} client hanno cambiato stato`);
        onClientStatusChange(changedClients);
      }
    } catch (error) {
      console.error('[ClientStatusMonitor] Errore durante il controllo dello stato dei client:', error);
    }
  };

  // Avvia il monitoraggio
  const startMonitoring = () => {
    if (!isActiveRef.current) {
      isActiveRef.current = true;
      intervalRef.current = setInterval(checkClientStatus, CLIENT_POLLING_INTERVAL);
      console.log('[ClientStatusMonitor] Monitoraggio avviato');
      
      // Esegui un controllo immediato
      checkClientStatus();
    }
  };

  // Ferma il monitoraggio
  const stopMonitoring = () => {
    if (isActiveRef.current) {
      isActiveRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      console.log('[ClientStatusMonitor] Monitoraggio fermato');
    }
  };

  // Gestisce l'avvio e l'arresto del monitoraggio quando il componente viene montato/smontato
  useEffect(() => {
    startMonitoring();
    
    // Cleanup quando il componente viene smontato
    return () => {
      stopMonitoring();
    };
  }, []);

  return {
    startMonitoring,
    stopMonitoring,
    isMonitoring: isActiveRef.current,
    checkNow: checkClientStatus
  };
};

export default useClientStatusMonitor;
