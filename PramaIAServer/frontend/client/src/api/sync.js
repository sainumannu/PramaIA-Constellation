import api from '../services/api';

// Esegue una scansione completa di tutti i file nelle cartelle monitorate
export const rescanAllFiles = async (client) => {
  try {
    console.log(`[DEBUG] Chiamata a ${client.endpoint}/monitor/rescan_all`);
    
    if (!client || !client.endpoint) {
      console.error('Client o endpoint non definito:', client);
      return {
        status: 'error',
        message: 'Client o endpoint non definito'
      };
    }
    
    // Sanifichiamo l'endpoint per assicurarci che non abbia slash doppi o finali
    const baseEndpoint = client.endpoint.replace(/\/+$/, '');
    const url = `${baseEndpoint}/monitor/rescan_all`;
    
    console.log(`[DEBUG] URL completo: ${url}`);
    
    // Opzioni avanzate per fetch
    const fetchOptions = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      // Aggiungiamo credentials: 'include' per permettere cookies per CORS
      credentials: 'include',
      // Timeout di 10 secondi
      signal: AbortSignal.timeout(10000)
    };
    
    console.log('[DEBUG] Invio richiesta con opzioni:', fetchOptions);
    const response = await fetch(url, fetchOptions);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Risposta non valida (${response.status}):`, errorText);
      throw new Error(`Errore HTTP ${response.status}: ${errorText || 'Nessun dettaglio disponibile'}`);
    }
    
    const result = await response.json();
    console.log('[DEBUG] Risposta ricevuta:', result);
    return result;
  } catch (e) {
    if (e.name === 'AbortError') {
      console.error('Timeout durante la richiesta di scansione completa');
      return {
        status: 'error',
        message: 'Timeout: il server non ha risposto entro il tempo limite'
      };
    }
    console.error('Errore dettagliato durante la scansione completa:', e);
    return {
      status: 'error',
      message: `Errore: ${e.message}`
    };
  }
};

// Ottieni lo stato di sincronizzazione da un client
export const fetchSyncStatus = async (client) => {
  try {
    const response = await fetch(`${client.endpoint}/monitor/sync-status`);
    if (!response.ok) throw new Error('Errore nel recupero dello stato di sincronizzazione');
    return await response.json();
  } catch (e) {
    console.error('Errore nel recupero dello stato di sincronizzazione:', e);
    return {
      status: 'error',
      message: `Errore: ${e.message}`,
      connection: {
        connected: false,
        consecutive_successes: 0,
        consecutive_failures: 0
      },
      reconciliation: {
        running: false,
        last_sync: {}
      },
      recovery: {
        enabled: false,
        auto_reconcile: false
      }
    };
  }
};

// Forza la riconciliazione per una cartella specifica
export const forceReconciliation = async (client, folderPath) => {
  try {
    const response = await fetch(`${client.endpoint}/monitor/reconcile?folder_path=${encodeURIComponent(folderPath)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) throw new Error('Errore durante la riconciliazione forzata');
    return await response.json();
  } catch (e) {
    console.error('Errore durante la riconciliazione forzata:', e);
    return {
      status: 'error',
      message: `Errore: ${e.message}`
    };
  }
};

// Forza l'invio degli eventi bufferizzati
export const forceSyncEvents = async (client) => {
  try {
    const response = await fetch(`${client.endpoint}/monitor/force-sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) throw new Error('Errore durante la sincronizzazione forzata');
    return await response.json();
  } catch (e) {
    console.error('Errore durante la sincronizzazione forzata:', e);
    return {
      status: 'error',
      message: `Errore: ${e.message}`
    };
  }
};

// Forza la registrazione del client
export const forceRegistration = async (client) => {
  try {
    const response = await fetch(`${client.endpoint}/monitor/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) throw new Error('Errore durante la registrazione forzata');
    return await response.json();
  } catch (e) {
    console.error('Errore durante la registrazione forzata:', e);
    return {
      status: 'error',
      message: `Errore: ${e.message}`
    };
  }
};

// Pulisce gli eventi duplicati o bloccati
export const cleanEvents = async (client) => {
  try {
    const response = await fetch(`${client.endpoint}/monitor/clean-events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      signal: AbortSignal.timeout(10000)
    });
    if (!response.ok) throw new Error('Errore durante la pulizia degli eventi');
    return await response.json();
  } catch (e) {
    console.error('Errore durante la pulizia degli eventi:', e);
    return {
      status: 'error',
      message: `Errore: ${e.message}`
    };
  }
};
