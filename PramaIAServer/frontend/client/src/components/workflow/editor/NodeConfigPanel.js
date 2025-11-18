import React, { useState, useEffect } from 'react';
import { X, Settings, Play, Save } from 'lucide-react';
import Form from '@rjsf/core';

const NodeConfigPanel = ({ node, onUpdateNode, onClose, onTest }) => {
  const [config, setConfig] = useState({});
  const [isValid, setIsValid] = useState(true);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (node) {
      setConfig(node.data.config || {});
    }
  }, [node]);

  if (!node) return null;

  // Gestisce i cambiamenti nella configurazione
  const handleConfigChange = (key, value) => {
    const newConfig = { ...config, [key]: value };
    setConfig(newConfig);
    
    // Validazione in tempo reale
    validateConfig(newConfig);
  };

  // Validazione della configurazione
  const validateConfig = (configToValidate) => {
    const newErrors = {};
    let valid = true;

    // Validazioni specifiche per tipo di nodo
    switch (node.type) {
      case 'textInput':
        if (!configToValidate.label || configToValidate.label.trim() === '') {
          newErrors.label = 'Il label è obbligatorio';
          valid = false;
        }
        break;
      
      case 'fileInput':
        if (!configToValidate.acceptedTypes || configToValidate.acceptedTypes.length === 0) {
          newErrors.acceptedTypes = 'Seleziona almeno un tipo di file';
          valid = false;
        }
        break;
      
      case 'llmProcessor':
        if (!configToValidate.model || configToValidate.model.trim() === '') {
          newErrors.model = 'Seleziona un modello LLM';
          valid = false;
        }
        if (!configToValidate.prompt || configToValidate.prompt.trim() === '') {
          newErrors.prompt = 'Il prompt è obbligatorio';
          valid = false;
        }
        break;
      
      case 'textProcessor':
        if (!configToValidate.operation) {
          newErrors.operation = 'Seleziona un\'operazione';
          valid = false;
        }
        break;
      
      case 'dataProcessor':
        if (!configToValidate.transformation) {
          newErrors.transformation = 'Seleziona una trasformazione';
          valid = false;
        }
        break;
    }

    setErrors(newErrors);
    setIsValid(valid);
  };

  // Salva la configurazione
  const handleSave = () => {
    if (isValid) {
      onUpdateNode(node.id, {
        ...node.data,
        config: config,
        configured: true
      });
      onClose();
    }
  };

  // Test del nodo
  const handleTest = () => {
    if (isValid && onTest) {
      onTest(node.id, config);
    }
  };

  // Renderizza i campi di configurazione basati sul tipo di nodo
  const renderConfigFields = () => {
    // Se è un nodo PDK (tipo che inizia con pdk_) e ha configSchema, usa react-jsonschema-form
    if (node.type && node.type.startsWith('pdk_') && node.data && node.data.configSchema) {
      return (
        <Form
          validator={undefined}
          schema={node.data.configSchema}
          formData={config}
          onChange={e => setConfig(e.formData)}
          onSubmit={e => {
            setConfig(e.formData);
            handleSave();
          }}
        >
          <button type="submit" className="mt-2 px-3 py-1 bg-blue-600 text-white rounded">Salva configurazione</button>
        </Form>
      );
    }
    switch (node.type) {
      case 'textInput':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Label Campo
              </label>
              <input
                type="text"
                value={config.label || ''}
                onChange={(e) => handleConfigChange('label', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.label ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Inserisci il testo..."
              />
              {errors.label && <p className="text-red-500 text-sm mt-1">{errors.label}</p>}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Valore Default
              </label>
              <input
                type="text"
                value={config.defaultValue || ''}
                onChange={(e) => handleConfigChange('defaultValue', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                id="required"
                checked={config.required || false}
                onChange={(e) => handleConfigChange('required', e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="required" className="text-sm text-gray-700">
                Campo obbligatorio
              </label>
            </div>
          </div>
        );

      case 'fileInput':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipi di File Accettati
              </label>
              <div className="space-y-2">
                {['pdf', 'txt', 'doc', 'docx', 'csv', 'json'].map(type => (
                  <div key={type} className="flex items-center">
                    <input
                      type="checkbox"
                      id={type}
                      checked={(config.acceptedTypes || []).includes(type)}
                      onChange={(e) => {
                        const types = config.acceptedTypes || [];
                        if (e.target.checked) {
                          handleConfigChange('acceptedTypes', [...types, type]);
                        } else {
                          handleConfigChange('acceptedTypes', types.filter(t => t !== type));
                        }
                      }}
                      className="mr-2"
                    />
                    <label htmlFor={type} className="text-sm text-gray-700 uppercase">
                      {type}
                    </label>
                  </div>
                ))}
              </div>
              {errors.acceptedTypes && <p className="text-red-500 text-sm mt-1">{errors.acceptedTypes}</p>}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dimensione Massima (MB)
              </label>
              <input
                type="number"
                value={config.maxSize || 10}
                onChange={(e) => handleConfigChange('maxSize', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
                max="100"
              />
            </div>
          </div>
        );

      case 'llmProcessor':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Modello LLM
              </label>
              <select
                value={config.model || ''}
                onChange={(e) => handleConfigChange('model', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.model ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="">Seleziona modello...</option>
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                <option value="claude-3">Claude 3</option>
                <option value="gemini-pro">Gemini Pro</option>
                <option value="ollama">Ollama (locale)</option>
              </select>
              {errors.model && <p className="text-red-500 text-sm mt-1">{errors.model}</p>}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Prompt
              </label>
              <textarea
                value={config.prompt || ''}
                onChange={(e) => handleConfigChange('prompt', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 h-32 resize-none ${
                  errors.prompt ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Inserisci il prompt per l'LLM..."
              />
              {errors.prompt && <p className="text-red-500 text-sm mt-1">{errors.prompt}</p>}
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Temperatura
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={config.temperature || 0.7}
                  onChange={(e) => handleConfigChange('temperature', parseFloat(e.target.value))}
                  className="w-full"
                />
                <span className="text-xs text-gray-500">{config.temperature || 0.7}</span>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Tokens
                </label>
                <input
                  type="number"
                  value={config.maxTokens || 1000}
                  onChange={(e) => handleConfigChange('maxTokens', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="100"
                  max="4000"
                />
              </div>
            </div>
          </div>
        );

      case 'textProcessor':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Operazione
              </label>
              <select
                value={config.operation || ''}
                onChange={(e) => handleConfigChange('operation', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.operation ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="">Seleziona operazione...</option>
                <option value="uppercase">Maiuscolo</option>
                <option value="lowercase">Minuscolo</option>
                <option value="trim">Rimuovi spazi</option>
                <option value="extract_emails">Estrai email</option>
                <option value="extract_urls">Estrai URL</option>
                <option value="word_count">Conta parole</option>
                <option value="summarize">Riassumi</option>
              </select>
              {errors.operation && <p className="text-red-500 text-sm mt-1">{errors.operation}</p>}
            </div>
          </div>
        );

      case 'textOutput':
      case 'fileOutput':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome Output
              </label>
              <input
                type="text"
                value={config.outputName || ''}
                onChange={(e) => handleConfigChange('outputName', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Nome del risultato..."
              />
            </div>
            
            {node.type === 'fileOutput' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Formato Output
                </label>
                <select
                  value={config.format || 'txt'}
                  onChange={(e) => handleConfigChange('format', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="txt">Testo (.txt)</option>
                  <option value="pdf">PDF (.pdf)</option>
                  <option value="json">JSON (.json)</option>
                  <option value="csv">CSV (.csv)</option>
                </select>
              </div>
            )}
          </div>
        );

      default:
        return (
          <div className="text-gray-500 text-center py-8">
            Configurazione non disponibile per questo tipo di nodo
          </div>
        );
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-lg border-l border-gray-200 z-50">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <Settings className="w-5 h-5 text-gray-500" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Configurazione Nodo
            </h3>
            <p className="text-sm text-gray-500">{node.data.name}</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-100 rounded-md transition-colors"
        >
          <X className="w-5 h-5 text-gray-500" />
        </button>
      </div>

      {/* Content */}
      <div className="p-4 flex-1 overflow-y-auto">
        {renderConfigFields()}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 space-y-2">
        {onTest && (
          <button
            onClick={handleTest}
            disabled={!isValid}
            className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Play className="w-4 h-4" />
            <span>Test Configurazione</span>
          </button>
        )}
        
        <button
          onClick={handleSave}
          disabled={!isValid}
          className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Save className="w-4 h-4" />
          <span>Salva Configurazione</span>
        </button>
      </div>
    </div>
  );
};

export default NodeConfigPanel;
