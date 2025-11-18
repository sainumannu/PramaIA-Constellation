// SchemaUtils.js
// Funzioni di utilità per la gestione degli schemi

export function isSchemaTypeMatch(type, schema) {
  if (!type || !schema) return false;
  const baseNodeType = type.split('/').pop().toLowerCase();
  if (schema.nodeId && baseNodeType.includes(schema.nodeId.toLowerCase())) return true;
  if (schema.nodeName) {
    const normalizedNodeName = schema.nodeName.toLowerCase().replace(/\s+/g, '_');
    if (baseNodeType.includes(normalizedNodeName)) return true;
  }
  if (schema.title) {
    const normalizedTitle = schema.title.toLowerCase().replace(/\s+/g, '_').replace(/configurazione\s+/i, '').replace(/configurazione\s+di\s+/i, '');
    if (baseNodeType.includes(normalizedTitle)) return true;
  }
  return false;
}

export function hasValidConfigSchema(configSchema) {
  if (!configSchema || typeof configSchema !== 'object') return false;
  const hasStandardProperties = configSchema.properties && typeof configSchema.properties === 'object' && Object.keys(configSchema.properties).length > 0;
  const metadataKeys = ['type', 'title', 'description', 'required', '$schema', 'properties'];
  const directConfigKeys = Object.keys(configSchema).filter(key => !metadataKeys.includes(key));
  const hasDirectConfig = directConfigKeys.length > 0;
  return hasStandardProperties || hasDirectConfig;
}

export function getSchemaToUse(schema) {
  if (schema && schema.properties && typeof schema.properties === 'object') {
    return schema;
  } else if (schema) {
    const metadataKeys = ['type', 'title', 'description', 'required', '$schema', 'nodeId', 'nodeName', 'uniqueKey'];
    const directKeys = Object.keys(schema).filter(key => !metadataKeys.includes(key));
    const properties = {};
    directKeys.forEach(key => {
      properties[key] = schema[key];
    });
    return {
      type: 'object',
      properties: properties,
      required: schema.required || []
    };
  } else {
    return {
      type: 'object',
      properties: {},
      required: []
    };
  }
}
