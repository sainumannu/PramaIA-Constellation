// ConfigValidator.js
// Validazione della configurazione del nodo

export function validateConfig(config, schema) {
  const newErrors = {};
  if (!schema) return true;
  if (schema.required) {
    schema.required.forEach(key => {
      if (!config[key] || config[key] === '') {
        newErrors[key] = 'Campo obbligatorio';
      }
    });
  }
  return newErrors;
}
