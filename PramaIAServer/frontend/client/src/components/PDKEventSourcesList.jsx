/**
 * PDK Event Sources Management Component
 */

import React, { useState, useEffect } from 'react';
import { PDK_SERVER_BASE_URL } from '../config/appConfig';
import { PDKTagManagementPanel, PDKTagBadge } from './PDKTagManagement';
import { usePDKEventSources } from '../hooks/usePDKData';

const PDKEventSourcesList = () => {
  const {
    eventSources,
    allEventSources,
    loading,
    error,
    updateFilters,
    resetFilters
  } = usePDKEventSources();

  const [filteredEventSources, setFilteredEventSources] = useState([]);
  const [selected, setSelected] = useState(null);
  const [showTagPanel, setShowTagPanel] = useState(false);
  const [sourceStatus, setSourceStatus] = useState({});

  // Update filtered sources when eventSources change
  useEffect(() => {
    setFilteredEventSources(eventSources);
  }, [eventSources]);

  const handleDetails = async (sourceId) => {
    setSelected(null);
    setError('');
    
    try {
      const response = await fetch(`${PDK_SERVER_BASE_URL}/api/event-sources/${sourceId}`);
      if (!response.ok) throw new Error('Failed to fetch event source details');
      
      const data = await response.json();
      setSelected(data);
    } catch (err) {
      console.error('Error fetching event source details:', err);
    }
  };

  const handleStartSource = async (sourceId) => {
    try {
      const response = await fetch(`${PDK_SERVER_BASE_URL}/api/event-sources/${sourceId}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          // Basic configuration - could be expanded with form
          config: {}
        })
      });
      
      if (!response.ok) throw new Error('Failed to start event source');
      
      // Update status
      setSourceStatus(prev => ({ ...prev, [sourceId]: 'starting' }));
      
      // Refresh status after a moment
      setTimeout(() => checkSourceStatus(sourceId), 2000);
    } catch (err) {
      console.error('Error starting event source:', err);
      setSourceStatus(prev => ({ ...prev, [sourceId]: 'error' }));
    }
  };

  const handleStopSource = async (sourceId) => {
    try {
      const response = await fetch(`${PDK_SERVER_BASE_URL}/api/event-sources/${sourceId}/stop`, {
        method: 'POST'
      });
      
      if (!response.ok) throw new Error('Failed to stop event source');
      
      setSourceStatus(prev => ({ ...prev, [sourceId]: 'stopping' }));
      setTimeout(() => checkSourceStatus(sourceId), 2000);
    } catch (err) {
      console.error('Error stopping event source:', err);
      setSourceStatus(prev => ({ ...prev, [sourceId]: 'error' }));
    }
  };

  const checkSourceStatus = async (sourceId) => {
    try {
      const response = await fetch(`${PDK_SERVER_BASE_URL}/api/event-sources/${sourceId}/status`);
      if (!response.ok) throw new Error('Failed to check status');
      
      const data = await response.json();
      setSourceStatus(prev => ({ ...prev, [sourceId]: data.status }));
    } catch (err) {
      console.error('Error checking status:', err);
      setSourceStatus(prev => ({ ...prev, [sourceId]: 'unknown' }));
    }
  };

  const getStatusBadge = (sourceId) => {
    const status = sourceStatus[sourceId] || 'stopped';
    const statusColors = {
      running: 'bg-green-100 text-green-800',
      stopped: 'bg-gray-100 text-gray-800',
      starting: 'bg-yellow-100 text-yellow-800',
      stopping: 'bg-orange-100 text-orange-800',
      error: 'bg-red-100 text-red-800',
      unknown: 'bg-gray-100 text-gray-600'
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status]}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const getLifecycleBadge = (lifecycle) => {
    const lifecycleColors = {
      'persistent': 'bg-blue-100 text-blue-800',
      'on-demand': 'bg-purple-100 text-purple-800',
      'scheduled': 'bg-indigo-100 text-indigo-800'
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${lifecycleColors[lifecycle] || 'bg-gray-100 text-gray-800'}`}>
        {lifecycle}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <span className="text-xl font-semibold text-purple-800">⚡ Event Sources PDK</span>
          <span className="ml-2 text-sm text-gray-600">
            ({filteredEventSources.length} di {allEventSources.length})
          </span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowTagPanel(!showTagPanel)}
            className={`px-4 py-2 rounded transition-colors ${
              showTagPanel 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {showTagPanel ? 'Nascondi Filtri' : 'Mostra Filtri Tag'}
          </button>
          <button
            onClick={resetFilters}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
          >
            Reset Filtri
          </button>
        </div>
      </div>

      {/* Tag Management Panel */}
      {showTagPanel && (
        <PDKTagManagementPanel
          items={allEventSources}
          onItemsFilter={setFilteredEventSources}
          showStats={true}
          showCloud={true}
        />
      )}

      {/* Loading and Error States */}
      {loading && (
        <div className="flex justify-center items-center py-8">
          <div className="text-purple-600">Caricamento event sources...</div>
        </div>
      )}
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Event Sources Table */}
      {!loading && filteredEventSources.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border border-gray-200 rounded-lg shadow">
            <thead>
              <tr className="bg-gray-100 text-gray-700 text-sm">
                <th className="px-4 py-3 text-left">Nome</th>
                <th className="px-4 py-3 text-left">ID</th>
                <th className="px-4 py-3 text-left">Descrizione</th>
                <th className="px-4 py-3 text-left">Tags</th>
                <th className="px-4 py-3 text-left">Lifecycle</th>
                <th className="px-4 py-3 text-left">Eventi</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Azioni</th>
              </tr>
            </thead>
            <tbody>
              {filteredEventSources.map(source => (
                <tr key={source.id} className="border-t hover:bg-gray-50">
                  <td className="px-4 py-3 font-semibold">{source.name}</td>
                  <td className="px-4 py-3 text-xs text-gray-500 font-mono">{source.id}</td>
                  <td className="px-4 py-3 text-sm max-w-xs">
                    <div className="truncate" title={source.description}>
                      {source.description}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {(source.tags || []).slice(0, 2).map(tag => (
                        <PDKTagBadge key={tag} tag={tag} size="sm" />
                      ))}
                      {source.tags && source.tags.length > 2 && (
                        <span className="text-xs text-gray-500">
                          +{source.tags.length - 2}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {getLifecycleBadge(source.lifecycle)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs">
                      {source.eventTypes?.length || 0}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {getStatusBadge(source.id)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button 
                        className="text-blue-600 hover:text-blue-800 underline text-sm" 
                        onClick={() => handleDetails(source.id)}
                      >
                        Dettagli
                      </button>
                      {sourceStatus[source.id] === 'running' ? (
                        <button 
                          className="text-red-600 hover:text-red-800 underline text-sm" 
                          onClick={() => handleStopSource(source.id)}
                        >
                          Stop
                        </button>
                      ) : (
                        <button 
                          className="text-green-600 hover:text-green-800 underline text-sm" 
                          onClick={() => handleStartSource(source.id)}
                        >
                          Start
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* No Results */}
      {!loading && filteredEventSources.length === 0 && allEventSources.length > 0 && (
        <div className="text-center py-8 text-gray-500">
          <div className="text-lg mb-2">Nessun event source trovato</div>
          <div className="text-sm">Prova a modificare i filtri di ricerca</div>
        </div>
      )}

      {/* Event Source Details Panel */}
      {selected && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-lg font-semibold">Event Source: {selected.name}</h3>
            <button
              onClick={() => setSelected(null)}
              className="text-gray-500 hover:text-gray-700"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
          
          {/* Tags and Lifecycle */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            {selected.tags && selected.tags.length > 0 && (
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">Tags:</div>
                <div className="flex flex-wrap gap-2">
                  {selected.tags.map(tag => (
                    <PDKTagBadge key={tag} tag={tag} />
                  ))}
                </div>
              </div>
            )}
            <div>
              <div className="text-sm font-medium text-gray-700 mb-2">Lifecycle:</div>
              {getLifecycleBadge(selected.lifecycle)}
            </div>
          </div>

          {/* Event Types */}
          {selected.eventTypes && selected.eventTypes.length > 0 && (
            <div className="mb-4">
              <div className="text-sm font-medium text-gray-700 mb-2">
                Event Types ({selected.eventTypes.length}):
              </div>
              <div className="space-y-2">
                {selected.eventTypes.map((eventType, index) => (
                  <div key={eventType.id || eventType.type || `event-${index}`} className="bg-white p-3 rounded border">
                    <div className="flex justify-between items-start mb-2">
                      <div className="font-medium">{eventType.name}</div>
                      <div className="flex flex-wrap gap-1">
                        {(eventType.tags || []).map((tag, tagIndex) => (
                          <PDKTagBadge key={`${eventType.type || index}-tag-${tagIndex}`} tag={tag} size="sm" variant="outline" />
                        ))}
                      </div>
                    </div>
                    <div className="text-sm text-gray-600 mb-2">{eventType.description}</div>
                    {eventType.outputs && eventType.outputs.length > 0 && (
                      <div className="text-xs text-gray-500">
                        Outputs: {eventType.outputs.map(o => o.name).join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Full JSON Details */}
          <details>
            <summary className="font-medium cursor-pointer text-gray-700 hover:text-gray-900">
              Configurazione JSON Completa
            </summary>
            <pre className="mt-2 text-xs bg-white p-3 rounded border overflow-x-auto">
              {JSON.stringify(selected, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
};

export default PDKEventSourcesList;
