import React, { useEffect, useState } from 'react';
import { 
  fetchSyncStatus, 
  forceReconciliation, 
  forceSyncEvents,
  forceRegistration,
  rescanAllFiles,
  cleanEvents
} from '../api/sync';



const SyncMonitoringPanel = ({ clients, selectedClient }) => {
  // Handler per la scansione completa di tutti i file
  const handleRescanAllFiles = async () => {
    if (!selectedClient || selectedClient.status === 'offline') {
      alert("Nessun client PDF Monitor attivo");
      return;
    }
    
    console.log(`[DEBUG] Avvio scansione completa per client:`, selectedClient);
    
    try {
      setLoading(true); // Mostra indicatore di caricamento
      const result = await rescanAllFiles(selectedClient);
      console.log(`[DEBUG] Risultato scansione:`, result);
      
      if (result.status === "success") {
        alert(result.message);
      } else {
        alert(`Errore: ${result.message || "Operazione fallita"}`);
      }
    } catch (e) {
      alert(`Errore durante la scansione: ${e.message}`);
      console.error("Errore dettagliato scansione completa:", e);
    } finally {
      setLoading(false); // Nascondi indicatore di caricamento
    }
  };

  // Handler per la pulizia degli eventi
  const handleCleanEvents = async () => {
    if (!selectedClient || selectedClient.status === 'offline') {
      alert("Nessun client PDF Monitor attivo");
      return;
    }
    
    console.log(`[DEBUG] Avvio pulizia eventi per client:`, selectedClient);
    
    try {
      setLoading(true); // Mostra indicatore di caricamento
      const result = await cleanEvents(selectedClient);
      console.log(`[DEBUG] Risultato pulizia:`, result);
      
      if (result.status === "success") {
        alert(result.message);
        // Ricarica lo stato dopo un breve ritardo
        setTimeout(loadSyncStatus, 1500);
      } else {
        alert(`Errore: ${result.message || "Operazione fallita"}`);
      }
    } catch (e) {
      alert(`Errore durante la pulizia degli eventi: ${e.message}`);
      console.error("Errore dettagliato pulizia eventi:", e);
    } finally {
      setLoading(false); // Nascondi indicatore di caricamento
    }
  };

  const [syncStatus, setSyncStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [processingFolder, setProcessingFolder] = useState(null);
  const [updateInterval, setUpdateInterval] = useState(10000); // 10 secondi di default

  // Aggiorna lo stato di sincronizzazione
  const loadSyncStatus = async () => {
    if (!selectedClient || selectedClient.status === 'offline') {
      setSyncStatus(null);
      return;
    }

    setLoading(true);
    try {
      const status = await fetchSyncStatus(selectedClient);
      setSyncStatus(status);
      setError('');
    } catch (e) {
      setError(`Errore nel recupero dello stato di sincronizzazione: ${e.message}`);
      console.error('Errore nel recupero dello stato di sincronizzazione:', e);
    } finally {
      setLoading(false);
    }
  };

  // Carica lo stato di sincronizzazione quando cambia il client selezionato
  useEffect(() => {
    loadSyncStatus();
    
    // Imposta un intervallo per ricaricare lo stato di sincronizzazione
    const interval = setInterval(loadSyncStatus, updateInterval);
    return () => clearInterval(interval);
  }, [selectedClient, updateInterval]);

  // Handler per la riconciliazione forzata
  const handleForceReconciliation = async (folderPath) => {
    if (!selectedClient || selectedClient.status === 'offline') {
      alert("Nessun client PDF Monitor attivo");
      return;
    }

    setProcessingFolder(folderPath);
    try {
      const result = await forceReconciliation(selectedClient, folderPath);
      if (result.status === "success") {
        alert(`Riconciliazione avviata con successo: ${result.message}`);
        // Ricarica lo stato dopo un breve ritardo per dare tempo alla riconciliazione di iniziare
        setTimeout(loadSyncStatus, 1500);
      } else {
        alert(`Errore: ${result.message || "Operazione fallita"}`);
      }
    } catch (e) {
      alert(`Errore durante la riconciliazione: ${e.message}`);
      console.error("Errore riconciliazione:", e);
    } finally {
      setProcessingFolder(null);
    }
  };

  // Handler per la sincronizzazione forzata
  const handleForceSyncEvents = async () => {
    if (!selectedClient || selectedClient.status === 'offline') {
      alert("Nessun client PDF Monitor attivo");
      return;
    }

    try {
      const result = await forceSyncEvents(selectedClient);
      if (result.status === "sync_triggered") {
        alert("Sincronizzazione eventi avviata con successo");
        // Ricarica lo stato dopo un breve ritardo
        setTimeout(loadSyncStatus, 1500);
      } else {
        alert(`Errore: ${result.message || "Operazione fallita"}`);
      }
    } catch (e) {
      alert(`Errore durante la sincronizzazione eventi: ${e.message}`);
      console.error("Errore sincronizzazione eventi:", e);
    }
  };

  // Handler per la registrazione forzata
  const handleForceRegistration = async () => {
    if (!selectedClient) {
      alert("Nessun client PDF Monitor selezionato");
      return;
    }

    try {
      const result = await forceRegistration(selectedClient);
      if (result.status === "success") {
        alert(`Registrazione completata: ${result.message}`);
        // Ricarica lo stato dopo un breve ritardo
        setTimeout(loadSyncStatus, 1500);
      } else {
        alert(`Errore: ${result.message || "Operazione fallita"}`);
      }
    } catch (e) {
      alert(`Errore durante la registrazione: ${e.message}`);
      console.error("Errore registrazione:", e);
    }
  };

  // Funzione per formattare un timestamp
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return "Mai";
    
    // Supporta sia stringhe ISO che Date objects
    const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
    return date.toLocaleString();
  };

  // Funzione per calcolare il tempo trascorso
  const timeAgo = (timestamp) => {
    if (!timestamp) return "";
    
    const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
    const now = new Date();
    const diffMs = now - date;
    
    const seconds = Math.floor(diffMs / 1000);
    if (seconds < 60) return `${seconds} secondi fa`;
    
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minuti fa`;
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} ore fa`;
    
    const days = Math.floor(hours / 24);
    return `${days} giorni fa`;
  };

  if (!selectedClient) {
    return (
      <div className="bg-white p-6 rounded shadow">
        <p className="text-center text-gray-500">Seleziona un client per visualizzare lo stato di sincronizzazione</p>
      </div>
    );
  }

  if (selectedClient.status === 'offline') {
    return (
      <div className="bg-white p-6 rounded shadow">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-blue-700">Stato Sincronizzazione</h2>
          <div>
            <button 
              className="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 text-xs"
              onClick={handleForceRegistration}
            >
              Forza Registrazione
            </button>
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded p-4 text-red-700 flex items-center gap-3">
          <span className="text-2xl">⚠️</span>
          <div>
            <p className="font-medium">Client Offline</p>
            <p className="text-sm">Il client è attualmente offline. Avvia il client o controlla la connessione.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded shadow space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-blue-700">Stato Sincronizzazione</h2>
        <div className="flex gap-2">
          <div className="flex items-center">
            <label htmlFor="update-interval" className="mr-2 text-sm text-gray-600">Aggiorna ogni:</label>
            <select 
              id="update-interval"
              className="text-sm border rounded px-2 py-1"
              value={updateInterval}
              onChange={(e) => setUpdateInterval(Number(e.target.value))}
            >
              <option value={5000}>5 secondi</option>
              <option value={10000}>10 secondi</option>
              <option value={30000}>30 secondi</option>
              <option value={60000}>1 minuto</option>
            </select>
          </div>
          <button 
            className="px-3 py-1 rounded bg-gray-100 text-gray-700 hover:bg-gray-200 text-xs"
            onClick={loadSyncStatus}
            disabled={loading}
          >
            {loading ? "Aggiornamento..." : "↻ Aggiorna"}
          </button>
          <button 
            className="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 text-xs"
            onClick={handleForceRegistration}
          >
            Forza Registrazione
          </button>
        </div>
      </div>
      
      {loading && !syncStatus && (
        <div className="text-center py-8">
          <p className="text-gray-500">Caricamento stato sincronizzazione...</p>
        </div>
      )}
      
      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-4 text-red-700">
          {error}
        </div>
      )}
      
      {syncStatus && (
        <div className="space-y-6">
          {/* Stato Connessione */}
          <div className="border rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-2 border-b">
              <h3 className="font-semibold">Stato Connessione</h3>
            </div>
            <div className="p-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Stato:</span>
                    <span className={syncStatus.connection.connected ? 'text-green-600' : 'text-red-600'}>
                      {syncStatus.connection.connected ? 'Connesso' : 'Disconnesso'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Successi consecutivi:</span>
                    <span>{syncStatus.connection.consecutive_successes}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Fallimenti consecutivi:</span>
                    <span>{syncStatus.connection.consecutive_failures}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Ultima connessione:</span>
                    <span title={syncStatus.connection.last_connected}>
                      {syncStatus.connection.last_connected ? timeAgo(syncStatus.connection.last_connected) : 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Ultima disconnessione:</span>
                    <span title={syncStatus.connection.last_disconnected}>
                      {syncStatus.connection.last_disconnected ? timeAgo(syncStatus.connection.last_disconnected) : 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Durata disconnessione:</span>
                    <span>{syncStatus.connection.disconnection_duration || 'N/A'}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Stato Riconciliazione */}
          <div className="border rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-2 border-b flex justify-between items-center">
              <h3 className="font-semibold">Servizio di Riconciliazione</h3>
              <span className={syncStatus.reconciliation.running ? 'text-green-600' : 'text-red-600'}>
                {syncStatus.reconciliation.running ? 'Attivo' : 'Inattivo'}
              </span>
            </div>
            <div className="p-4">
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-600">Intervallo di sincronizzazione:</span>
                  <span>{syncStatus.reconciliation.sync_interval} secondi</span>
                </div>
                
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-600">Cartelle monitorate:</span>
                  <button 
                    className="px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 text-xs"
                    onClick={handleForceSyncEvents}
                  >
                    Forza Sync Eventi
                  </button>
                </div>
                
                <div className="border rounded overflow-hidden mt-2">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="bg-gray-100">
                        <th className="px-3 py-1 text-left">Cartella</th>
                        <th className="px-3 py-1 text-center">Stato</th>
                        <th className="px-3 py-1 text-left">Ultima Sincronizzazione</th>
                        <th className="px-3 py-1 text-right">Azioni</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedClient.folders && selectedClient.folders.length > 0 ? (
                        selectedClient.folders.map((folder, index) => {
                          const lastSync = syncStatus.reconciliation.last_sync[folder] || 
                                          syncStatus.reconciliation.last_sync['periodic'];
                          // Verifica se la cartella è attivamente monitorata
                          const isActivelyMonitored = syncStatus.reconciliation.active_folders && 
                                                    syncStatus.reconciliation.active_folders.includes(folder);
                          return (
                            <tr key={index} className="border-t">
                              <td className="px-3 py-2 font-mono text-xs">
                                {folder}
                              </td>
                              <td className="px-3 py-2 text-center">
                                {isActivelyMonitored ? (
                                  <span className="px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-xs">
                                    Attivo
                                  </span>
                                ) : (
                                  <span className="px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 text-xs" 
                                    title="La cartella è configurata ma non attivamente monitorata. La riconciliazione periodica non verrà eseguita.">
                                    Inattivo
                                  </span>
                                )}
                              </td>
                              <td className="px-3 py-2">
                                {lastSync ? (
                                  <span title={formatTimestamp(lastSync)}>
                                    {timeAgo(lastSync)}
                                  </span>
                                ) : (
                                  <span className="text-gray-400">Mai</span>
                                )}
                              </td>
                              <td className="px-3 py-2 text-right">
                                <button
                                  className="px-2 py-1 rounded bg-green-100 text-green-700 hover:bg-green-200 text-xs"
                                  onClick={() => handleForceReconciliation(folder)}
                                  disabled={processingFolder === folder}
                                >
                                  {processingFolder === folder ? "In corso..." : "Forza Riconciliazione"}
                                </button>
                              </td>
                            </tr>
                          );
                        })
                      ) : (
                        <tr>
                          <td colSpan={3} className="px-3 py-3 text-center text-gray-500">
                            Nessuna cartella configurata
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
                
                <div className="mt-4 text-xs text-gray-600 bg-yellow-50 p-3 rounded border border-yellow-200">
                  <p><strong>Nota sulla riconciliazione:</strong> Solo le cartelle con stato <span className="px-1 py-0.5 rounded-full bg-green-100 text-green-700">Attivo</span> saranno incluse nella riconciliazione periodica automatica. 
                  Le cartelle inattive richiedono una riconciliazione manuale.</p>
                  <p className="mt-1">Per attivare il monitoraggio di una cartella, usa il pulsante "Start" nella scheda "Client PDF Monitor".</p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Pulsante scansione completa */}
          <div className="border rounded-lg overflow-hidden mb-4">
            <div className="bg-gray-50 px-4 py-2 border-b flex justify-between items-center">
              <h3 className="font-semibold">Manutenzione</h3>
            </div>
            <div className="p-4 flex gap-4">
              <div>
                <button
                  className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 text-sm"
                  onClick={handleRescanAllFiles}
                  disabled={!selectedClient || selectedClient.status === 'offline'}
                  title="Genera eventi per tutti i file PDF nelle cartelle monitorate"
                >
                  🗂️ Scansiona tutti i file
                </button>
                <p className="mt-2 text-xs text-gray-600">Genera eventi 'created' per tutti i file PDF nelle cartelle monitorate, anche se già presenti.</p>
              </div>
              <div>
                <button
                  className="px-4 py-2 rounded bg-orange-600 text-white hover:bg-orange-700 text-sm"
                  onClick={handleCleanEvents}
                  disabled={!selectedClient || selectedClient.status === 'offline'}
                  title="Pulisce gli eventi duplicati e aggiorna quelli bloccati"
                >
                  🧹 Pulisci eventi
                </button>
                <p className="mt-2 text-xs text-gray-600">Rimuove gli eventi duplicati e aggiorna lo stato degli eventi bloccati.</p>
              </div>
            </div>
          </div>
          {/* Stato Recovery Sync */}
          <div className="border rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-2 border-b flex justify-between items-center">
              <h3 className="font-semibold">Recovery Sync</h3>
              <span className={syncStatus.recovery.enabled ? 'text-green-600' : 'text-red-600'}>
                {syncStatus.recovery.enabled ? 'Abilitato' : 'Disabilitato'}
              </span>
            </div>
            <div className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-600">Riconciliazione Automatica:</span>
                <span>{syncStatus.recovery.auto_reconcile ? 'Attiva' : 'Inattiva'}</span>
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Il recovery sync si attiva automaticamente quando viene ripristinata la connessione dopo un'interruzione. 
                Verifica tutti i file nelle cartelle monitorate e sincronizza eventuali modifiche apportate durante la disconnessione.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SyncMonitoringPanel;
