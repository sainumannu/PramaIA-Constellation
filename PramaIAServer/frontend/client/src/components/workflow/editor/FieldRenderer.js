// FieldRenderer.js
// Rendering dei campi dinamici per NodeConfigForm
import React from 'react';

export function FieldRenderer({ keyName, schema, value, errors, onChange }) {
  const fieldSchema = schema.properties?.[keyName] || {};
  const type = fieldSchema.type || 'string';
  const description = fieldSchema.description || '';
  const required = schema.required?.includes(keyName) || false;

  switch (type) {
    case 'string':
      if (fieldSchema.enum) {
        return (
          <div key={keyName} className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {fieldSchema.title || keyName}
              {required && <span className="text-red-500 ml-1">*</span>}
            </label>
            {description && (
              <p className="text-xs text-gray-500 mb-2">{description}</p>
            )}
            <select
              value={value}
              onChange={e => onChange(e.target.value)}
              className={`w-full px-3 py-2 border rounded-md ${errors[keyName] ? 'border-red-500' : 'border-gray-300'}`}
            >
              <option value="">Seleziona...</option>
              {fieldSchema.enum.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
            {errors[keyName] && (
              <p className="text-red-500 text-xs mt-1">{errors[keyName]}</p>
            )}
          </div>
        );
      }
      // ...existing code for string fields...
      return (
        <div key={keyName} className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {fieldSchema.title || keyName}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
          {description && (
            <p className="text-xs text-gray-500 mb-2">{description}</p>
          )}
          <input
            type="text"
            value={value}
            onChange={e => onChange(e.target.value)}
            placeholder={fieldSchema.default || ''}
            className={`w-full px-3 py-2 border rounded-md ${errors[keyName] ? 'border-red-500' : 'border-gray-300'}`}
          />
          {errors[keyName] && (
            <p className="text-red-500 text-xs mt-1">{errors[keyName]}</p>
          )}
        </div>
      );
    case 'number':
    case 'integer':
      return (
        <div key={keyName} className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {fieldSchema.title || keyName}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
          {description && (
            <p className="text-xs text-gray-500 mb-2">{description}</p>
          )}
          <input
            type="number"
            value={value}
            onChange={e => onChange(type === 'integer' ? parseInt(e.target.value) || 0 : parseFloat(e.target.value) || 0)}
            min={fieldSchema.minimum}
            max={fieldSchema.maximum}
            step={type === 'integer' ? 1 : 0.1}
            className={`w-full px-3 py-2 border rounded-md ${errors[keyName] ? 'border-red-500' : 'border-gray-300'}`}
          />
          {errors[keyName] && (
            <p className="text-red-500 text-xs mt-1">{errors[keyName]}</p>
          )}
        </div>
      );
    case 'boolean':
      return (
        <div key={keyName} className="mb-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={value}
              onChange={e => onChange(e.target.checked)}
              className="mr-2"
            />
            <span className="text-sm font-medium text-gray-700">
              {fieldSchema.title || keyName}
              {required && <span className="text-red-500 ml-1">*</span>}
            </span>
          </label>
          {description && (
            <p className="text-xs text-gray-500 mt-1 ml-6">{description}</p>
          )}
          {errors[keyName] && (
            <p className="text-red-500 text-xs mt-1 ml-6">{errors[keyName]}</p>
          )}
        </div>
      );
    case 'array':
      return (
        <div key={keyName} className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {fieldSchema.title || keyName}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
          {description && (
            <p className="text-xs text-gray-500 mb-2">{description}</p>
          )}
          <textarea
            value={Array.isArray(value) ? value.join('\n') : value}
            onChange={e => onChange(e.target.value.split('\n').filter(line => line.trim()))}
            placeholder="Un elemento per riga"
            rows={3}
            className={`w-full px-3 py-2 border rounded-md ${errors[keyName] ? 'border-red-500' : 'border-gray-300'}`}
          />
          {errors[keyName] && (
            <p className="text-red-500 text-xs mt-1">{errors[keyName]}</p>
          )}
        </div>
      );
    default:
      return (
        <div key={keyName} className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {fieldSchema.title || keyName}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
          {description && (
            <p className="text-xs text-gray-500 mb-2">{description}</p>
          )}
          <textarea
            value={typeof value === 'object' ? JSON.stringify(value, null, 2) : value}
            onChange={e => {
              try {
                onChange(JSON.parse(e.target.value));
              } catch {
                onChange(e.target.value);
              }
            }}
            rows={3}
            className={`w-full px-3 py-2 border rounded-md font-mono text-sm ${errors[keyName] ? 'border-red-500' : 'border-gray-300'}`}
          />
          {errors[keyName] && (
            <p className="text-red-500 text-xs mt-1">{errors[keyName]}</p>
          )}
        </div>
      );
  }
}
