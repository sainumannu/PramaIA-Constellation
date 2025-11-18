import React, { useState, useEffect } from 'react';

const EdgeConfigPanel = ({ edge, onUpdateEdge, onDeleteEdge, onClose }) => {
  const [config, setConfig] = useState({
    label: '',
    animated: true,
    style: {
      stroke: '#4F46E5',
      strokeWidth: 2
    },
    type: 'smoothstep',
    condition: '', // Condizione per passaggio dati (futuro)
    transform: '', // Trasformazione dati (futuro)
  });
  const [isValid, setIsValid] = useState(true);

  useEffect(() => {
    if (edge) {
      setConfig({
        label: edge.label || '',
        animated: edge.animated ?? true,
        style: {
          stroke: edge.style?.stroke || '#4F46E5',
          strokeWidth: edge.style?.strokeWidth || 2
        },
        type: edge.type || 'smoothstep',
        condition: edge.data?.condition || '',
        transform: edge.data?.transform || '',
      });
    }
  }, [edge]);

  if (!edge) return null;

  const handleConfigChange = (key, value) => {
    const newConfig = { ...config };
    
    if (key.includes('.')) {
      // Handle nested properties like 'style.stroke'
      const [parent, child] = key.split('.');
      newConfig[parent] = {
        ...newConfig[parent],
        [child]: value
      };
    } else {
      newConfig[key] = value;
    }
    
    setConfig(newConfig);
    setIsValid(true);
  };

  const handleSave = () => {
    if (!isValid) return;

    onUpdateEdge(edge.id, {
      label: config.label,
      animated: config.animated,
      style: config.style,
      type: config.type,
      condition: config.condition,
      transform: config.transform,
    });
  };

  const handleDelete = () => {
    if (window.confirm('Sei sicuro di voler eliminare questa connessione?')) {
      onDeleteEdge(edge.id);
      onClose();
    }
  };

  const edgeTypeOptions = [
    { value: 'default', label: 'Linea Diretta' },
    { value: 'straight', label: 'Linea Retta' },
    { value: 'step', label: 'Linea a Gradini' },
    { value: 'smoothstep', label: 'Linea Curva' },
    { value: 'bezier', label: 'Curva Bezier' }
  ];

  const colorOptions = [
    { value: '#4F46E5', label: 'Blu', color: '#4F46E5' },
    { value: '#059669', label: 'Verde', color: '#059669' },
    { value: '#DC2626', label: 'Rosso', color: '#DC2626' },
    { value: '#D97706', label: 'Arancione', color: '#D97706' },
    { value: '#7C3AED', label: 'Viola', color: '#7C3AED' },
    { value: '#374151', label: 'Grigio', color: '#374151' }
  ];

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-white border-l border-gray-200 shadow-lg z-50 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-green-600 text-lg">🔗</span>
            <h2 className="text-lg font-semibold text-gray-900">
              Configurazione Connessione
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 rounded text-lg"
          >
            ✕
          </button>
        </div>
        
        {/* Info connessione */}
        <div className="mt-3 p-3 bg-gray-50 rounded-lg">
          <div className="text-sm">
            <div className="font-medium text-gray-900">Collegamento:</div>
            <div className="text-gray-600 mt-1">
              <span className="font-mono text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                {edge.source}
              </span>
              <span className="mx-2">→</span>
              <span className="font-mono text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                {edge.target}
              </span>
            </div>
            {edge.sourceHandle && edge.targetHandle && (
              <div className="text-xs text-gray-500 mt-1">
                Porte: {edge.sourceHandle} → {edge.targetHandle}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-6">
        {/* Aspetto Visuale */}
        <div>
          <h3 className="text-md font-medium text-gray-900 mb-3">
            <span className="mr-2">👁️</span>
            Aspetto Visuale
          </h3>
          
          {/* Label */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Etichetta (opzionale)
            </label>
            <input
              type="text"
              value={config.label}
              onChange={(e) => handleConfigChange('label', e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Inserisci un'etichetta per la connessione"
            />
          </div>

          {/* Tipo di linea */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tipo di Linea
            </label>
            <select
              value={config.type}
              onChange={(e) => handleConfigChange('type', e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {edgeTypeOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Colore */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Colore
            </label>
            <div className="grid grid-cols-3 gap-2">
              {colorOptions.map(option => (
                <button
                  key={option.value}
                  onClick={() => handleConfigChange('style.stroke', option.value)}
                  className={`p-2 rounded-md border-2 text-xs font-medium transition-all ${
                    config.style.stroke === option.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div
                    className="w-4 h-4 rounded mx-auto mb-1"
                    style={{ backgroundColor: option.color }}
                  />
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Spessore */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Spessore: {config.style.strokeWidth}px
            </label>
            <input
              type="range"
              min="1"
              max="8"
              value={config.style.strokeWidth}
              onChange={(e) => handleConfigChange('style.strokeWidth', parseInt(e.target.value))}
              className="w-full"
            />
          </div>

          {/* Animazione */}
          <div className="mb-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={config.animated}
                onChange={(e) => handleConfigChange('animated', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">
                Animazione fluente
              </span>
            </label>
          </div>
        </div>

        {/* Configurazione Avanzata */}
        <div>
          <h3 className="text-md font-medium text-gray-900 mb-3">
            ⚙️ Configurazione Avanzata
          </h3>
          
          {/* Condizione (futuro) */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Condizione di Passaggio (futuro)
            </label>
            <textarea
              value={config.condition}
              onChange={(e) => handleConfigChange('condition', e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows="2"
              placeholder="es: output.confidence > 0.8"
              disabled
            />
            <p className="text-xs text-gray-500 mt-1">
              Questa funzionalità sarà disponibile in futuro
            </p>
          </div>

          {/* Trasformazione (futuro) */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Trasformazione Dati (futuro)
            </label>
            <textarea
              value={config.transform}
              onChange={(e) => handleConfigChange('transform', e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows="2"
              placeholder="es: { text: input.content, metadata: input.meta }"
              disabled
            />
            <p className="text-xs text-gray-500 mt-1">
              Questa funzionalità sarà disponibile in futuro
            </p>
          </div>
        </div>

        {/* Preview */}
        <div>
          <h3 className="text-md font-medium text-gray-900 mb-3">
            👁️ Anteprima
          </h3>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center">
              <div className="flex items-center gap-4">
                <div className="w-8 h-8 bg-blue-100 rounded border border-blue-200 flex items-center justify-center">
                  <span className="text-xs font-medium text-blue-600">A</span>
                </div>
                <div
                  className="flex-1 h-0 border-t-2 min-w-[100px] relative"
                  style={{
                    borderColor: config.style.stroke,
                    borderWidth: `${config.style.strokeWidth}px`,
                    animation: config.animated ? 'pulse 2s infinite' : 'none'
                  }}
                >
                  {config.label && (
                    <span 
                      className="absolute top-[-20px] left-1/2 transform -translate-x-1/2 text-xs bg-white px-1 border rounded"
                      style={{ color: config.style.stroke }}
                    >
                      {config.label}
                    </span>
                  )}
                </div>
                <div className="w-8 h-8 bg-green-100 rounded border border-green-200 flex items-center justify-center">
                  <span className="text-xs font-medium text-green-600">B</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="sticky bottom-0 bg-white border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            disabled={!isValid}
            className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <span>💾</span>
            Salva
          </button>
          <button
            onClick={handleDelete}
            className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 flex items-center gap-2"
          >
            <span>🗑️</span>
            Elimina
          </button>
        </div>
      </div>
    </div>
  );
};

export default EdgeConfigPanel;
