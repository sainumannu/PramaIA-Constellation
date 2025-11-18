// NodeConfigForm.js
// Componente per la configurazione dinamica dei nodi basata su schema

import React, { useEffect } from 'react';
import { fixSchemaForNode } from './nodeSchemaFixes';
import { FieldRenderer } from './FieldRenderer';
import { registerSchemaDebug } from './SchemaDebugTools';
import { useConfigState } from './ConfigState';
import { validateConfig } from './ConfigValidator';
import { isSchemaTypeMatch, hasValidConfigSchema, getSchemaToUse } from './SchemaUtils';

const NodeConfigForm = ({ node, onSave, onCancel }) => {
  // Stato e errori gestiti da hook custom
  const { config, setConfig, errors, setErrors } = useConfigState(node?.data?.config || node?.data?.defaultConfig);

  // Debug globale
  if (window.__NODE_SCHEMA_DEBUG) {
    window.__NODE_SCHEMA_DEBUG.logAccess(node);
  }

  // Inizializza funzioni di debug globale (una sola volta)
  registerSchemaDebug();

  // Patch schema se necessario
  useEffect(() => {
    if (node?.data?.configSchema) {
      const nodeId = node?.id;
      const nodeType = node?.type;
      const schemaId = node?.data?.configSchema?.nodeId;
      try {
        fixSchemaForNode(nodeType, schemaId, node);
      } catch (err) {
        console.warn('[NodeConfigForm] nodeSchemaFixes threw error:', err);
      }
    }
    // Aggiorna config se cambia il nodo
    if (node?.data?.config) {
      setConfig({ ...node.data.config });
    } else if (node?.data?.defaultConfig) {
      setConfig({ ...node.data.defaultConfig });
    }
  }, [node]);

  // Cambio valore campo
  const handleFieldChange = (key, newValue) => {
    setConfig(prev => ({ ...prev, [key]: newValue }));
    if (errors[key] && newValue) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[key];
        return newErrors;
      });
    }
  };

  // Validazione e salvataggio
  const handleSave = () => {
    const schema = node.data?.configSchema;
    const newErrors = validateConfig(config, schema);
    setErrors(newErrors);
    if (Object.keys(newErrors).length === 0) {
      onSave(config);
    }
  };

  // Se non c'è schema o è vuoto, mostra configurazione JSON manuale
  const configSchema = node.data?.configSchema;
  const validSchema = hasValidConfigSchema(configSchema);

  if (!validSchema) {
    return (
      <div className="space-y-4">
        <div className="text-sm text-gray-600">
          {!node.data?.configSchema 
            ? "Questo nodo non ha uno schema di configurazione definito."
            : "Questo nodo non ha parametri configurabili."
          }
          {node.data?.config && Object.keys(node.data.config).length > 0 && (
            <span>
              <br />Puoi modificare la configurazione esistente in formato JSON:
            </span>
          )}
        </div>
        
        {/* Mostra textarea JSON solo se c'è già una configurazione o se non c'è schema */}
        {(!node.data?.configSchema || (node.data?.config && Object.keys(node.data.config).length > 0)) && (
          <>
            <textarea
              value={JSON.stringify(config, null, 2)}
              onChange={(e) => {
                try {
                  setConfig(JSON.parse(e.target.value));
                  setErrors({});
                } catch (err) {
                  setErrors({ json: 'JSON non valido' });
                }
              }}
              rows={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm"
            />
            {errors.json && (
              <p className="text-red-500 text-xs">{errors.json}</p>
            )}
          </>
        )}
        
        <div className="flex justify-end space-x-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
          >
            Chiudi
          </button>
          {(!node.data?.configSchema || (node.data?.config && Object.keys(node.data.config).length > 0)) && (
            <button
              onClick={handleSave}
              disabled={errors.json}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
            >
              Salva
            </button>
          )}
        </div>
      </div>
    );
  }

  // Ottieni schema normalizzato e proprietà
  const schemaToUse = getSchemaToUse(configSchema);
  const properties = schemaToUse.properties || {};

  return (
    <div className="space-y-4">
      <div className="text-sm text-gray-600">
        Configura i parametri per questo nodo:
      </div>
      {Object.keys(properties).map(key => (
        <FieldRenderer
          key={key}
          keyName={key}
          schema={schemaToUse}
          value={config[key] || ''}
          errors={errors}
          onChange={newValue => handleFieldChange(key, newValue)}
        />
      ))}
      <div className="flex justify-end space-x-2 pt-4 border-t">
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
        >
          Annulla
        </button>
        <button
          onClick={handleSave}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Salva Configurazione
        </button>
      </div>
    </div>
  );
// ...existing code...
}

// ...existing code...
export default NodeConfigForm;
