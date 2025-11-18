import React from 'react';

function EventsTable({ events }) {
  return (
    <div>
      <h4 className="text-lg font-medium mb-3">📋 Eventi Recenti</h4>
      {events.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full border border-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Timestamp</th>
                <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Tipo</th>
                <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">File</th>
                <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Status</th>
                <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Retry</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {events.map((event, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-sm text-gray-600">
                    {new Date(event.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-1 text-xs rounded ${
                      event.event_type === 'created' ? 'bg-green-100 text-green-700' :
                      event.event_type === 'modified' ? 'bg-blue-100 text-blue-700' :
                      event.event_type === 'deleted' ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {event.event_type}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-sm text-gray-900">
                    {event.file_path.split('/').pop() || event.file_path.split('\\').pop()}
                  </td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-1 text-xs rounded ${
                      event.processed ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {event.processed ? 'Processato' : 'Pending'}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-sm text-gray-600">
                    {event.retry_count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-gray-500 text-center py-8">
          Nessun evento disponibile
        </div>
      )}
    </div>
  );
}

export default EventsTable;
