import React, { useState } from 'react';
import BaseNode from './BaseNode';

const OutlookEmailNode = ({ id, data, selected }) => {
  const [config, setConfig] = useState(data.config || {
    action: 'send', // send, read, search
    to: '',
    subject: '',
    body: '',
    searchQuery: '',
    folder: 'inbox'
  });

  const handleConfigChange = (field, value) => {
    const newConfig = { ...config, [field]: value };
    setConfig(newConfig);
    
    // Update the node data
    if (data.onConfigChange) {
      data.onConfigChange(id, { ...data, config: newConfig });
    }
  };

  const nodeConfig = (
    <div className="space-y-3">
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">Azione</label>
        <select
          value={config.action}
          onChange={(e) => handleConfigChange('action', e.target.value)}
          className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="send">Invia Email</option>
          <option value="read">Leggi Email</option>
          <option value="search">Cerca Email</option>
        </select>
      </div>

      {config.action === 'send' && (
        <>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Destinatario</label>
            <input
              type="email"
              value={config.to}
              onChange={(e) => handleConfigChange('to', e.target.value)}
              placeholder="email@example.com"
              className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Oggetto</label>
            <input
              type="text"
              value={config.subject}
              onChange={(e) => handleConfigChange('subject', e.target.value)}
              placeholder="Oggetto dell'email"
              className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Corpo</label>
            <textarea
              value={config.body}
              onChange={(e) => handleConfigChange('body', e.target.value)}
              placeholder="Testo dell'email"
              rows={3}
              className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
            />
          </div>
        </>
      )}

      {(config.action === 'read' || config.action === 'search') && (
        <>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Cartella</label>
            <select
              value={config.folder}
              onChange={(e) => handleConfigChange('folder', e.target.value)}
              className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="inbox">Posta in arrivo</option>
              <option value="sent">Posta inviata</option>
              <option value="drafts">Bozze</option>
              <option value="deleted">Eliminati</option>
            </select>
          </div>
          {config.action === 'search' && (
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Query di ricerca</label>
              <input
                type="text"
                value={config.searchQuery}
                onChange={(e) => handleConfigChange('searchQuery', e.target.value)}
                placeholder="es: from:example@email.com"
                className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          )}
        </>
      )}
    </div>
  );

  return (
    <BaseNode
      data={{
        name: data.name || 'Outlook Email',
        description: data.description || `${config.action === 'send' ? 'Invia' : config.action === 'read' ? 'Leggi' : 'Cerca'} email con Outlook`,
        config: config
      }}
      icon="📧"
      selected={selected}
      bgColor="bg-blue-50"
      borderColor={selected ? "border-blue-500" : "border-blue-300"}
      textColor="text-blue-900"
      nodeConfig={nodeConfig}
    />
  );
};

export default OutlookEmailNode;
