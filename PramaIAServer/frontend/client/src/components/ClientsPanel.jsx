import React from 'react';
import {
  startDocumentMonitorClient,
  pauseDocumentMonitorClient,
  stopDocumentMonitorClient,
  addFolderToClient,
  removeFolderFromClient,
  toggleFolderAutostart
} from '../api/monitoring';

const ClientsPanel = ({ 
  clients, 
  loading, 
  error, 
  selectedClient, 
  handleSelectClient, 
  loadClients 
}) => {
  // Handler azioni
  const handleStart = async (client) => {
    const res = await startDocumentMonitorClient(client);
    alert(res.message || 'START inviato');
    loadClients();
  };
  
  const handlePause = async (client) => {
    const res = await pauseDocumentMonitorClient(client);
    alert(res.message || 'PAUSE inviato');
    loadClients();
  };
  
  const handleStop = async (client) => {
    const res = await stopDocumentMonitorClient(client);
    alert(res.message || 'STOP inviato');
    loadClients();
  };
  
  const handleAddFolder = async (client) => {
    const folder = prompt('Inserisci percorso cartella da aggiungere:');
    if (folder) {
      const res = await addFolderToClient(client, folder);
      alert(res.message || 'Cartella aggiunta');
      loadClients();
    }
  };
  
  const handleRemoveFolder = async (client, folder) => {
    const res = await removeFolderFromClient(client, folder);
    alert(res.message || 'Cartella rimossa');
    loadClients();
  };
  
  const handleToggleAutostart = async (client, folder, currentStatus) => {
    // Inverti lo stato attuale
    const enable = !currentStatus;
    const res = await toggleFolderAutostart(client, folder, enable);
    const message = enable ? 'Autostart abilitato' : 'Autostart disabilitato';
    alert(res.message || message);
    loadClients();
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4 text-blue-700">PDF Monitor - Client Registrati</h2>
      {loading && <div className="text-center text-gray-500">Caricamento...</div>}
      {error && <div className="text-center text-red-500">{error}</div>}
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm border">
          <thead>
            <tr className="bg-gray-100">
              <th className="px-2 py-1">Nome</th>
              <th className="px-2 py-1">Endpoint</th>
              <th className="px-2 py-1">Stato</th>
              <th className="px-2 py-1">Cartelle monitorate</th>
              <th className="px-2 py-1">Azioni</th>
            </tr>
          </thead>
          <tbody>
            {(!loading && clients.length === 0) ? (
              <tr><td colSpan={5} className="text-center">Nessun client registrato</td></tr>
            ) : (
              clients.map(client => (
                <tr 
                  key={client.id} 
                  className={`border-b ${selectedClient && selectedClient.id === client.id ? 'bg-blue-50' : ''}`}
                  onClick={() => handleSelectClient(client)}
                  style={{ cursor: 'pointer' }}
                >
                  <td className="px-2 py-1 font-semibold">{client.name}</td>
                  <td className="px-2 py-1 font-mono">{client.endpoint}</td>
                  <td className="px-2 py-1">
                    <span className={
                      client.status === 'online' ? 'text-green-600' :
                      client.status === 'paused' ? 'text-yellow-600' :
                      'text-red-600'
                    }>
                      {client.status}
                    </span>
                  </td>
                  <td className="px-2 py-1 align-top min-w-[220px]">
                    <div className="flex flex-col gap-2">
                      <ul className="list-disc ml-4">
                        {client.folders && client.folders.map(f => (
                          <li key={f} className="flex items-center gap-2">
                            <span>{f}</span>
                            <div className="flex items-center ml-auto gap-2">
                              <label className="inline-flex items-center cursor-pointer">
                                <input 
                                  type="checkbox" 
                                  className="sr-only peer"
                                  checked={client.autostart_folders && client.autostart_folders.includes(f)}
                                  onChange={() => handleToggleAutostart(client, f, client.autostart_folders && client.autostart_folders.includes(f))}
                                />
                                <div className="relative w-8 h-4 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-blue-600"></div>
                                <span className="ml-1 text-xs text-gray-600">Autostart</span>
                              </label>
                              <button className="text-xs text-red-500 hover:underline" onClick={(e) => { e.stopPropagation(); handleRemoveFolder(client, f); }}>Rimuovi</button>
                            </div>
                          </li>
                        ))}
                      </ul>
                      <button
                        className="mt-2 px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 text-xs shadow self-start"
                        onClick={(e) => { e.stopPropagation(); handleAddFolder(client); }}
                        disabled={loading}
                      >
                        + Aggiungi cartella
                      </button>
                    </div>
                  </td>
                  <td className="px-2 py-1 flex gap-2">
                    <button 
                      className="px-2 py-1 rounded bg-green-100 text-green-700 disabled:opacity-50" 
                      disabled={!client.canStart} 
                      onClick={(e) => { e.stopPropagation(); handleStart(client); }}
                    >
                      Start
                    </button>
                    <button 
                      className="px-2 py-1 rounded bg-yellow-100 text-yellow-700 disabled:opacity-50" 
                      disabled={!client.canPause} 
                      onClick={(e) => { e.stopPropagation(); handlePause(client); }}
                    >
                      Pause
                    </button>
                    <button 
                      className="px-2 py-1 rounded bg-red-100 text-red-700 disabled:opacity-50" 
                      disabled={!client.canStop} 
                      onClick={(e) => { e.stopPropagation(); handleStop(client); }}
                    >
                      Stop
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ClientsPanel;
