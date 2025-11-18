// SchemaDebugTools.js
// Funzioni di debug globale per NodeConfigForm

export function registerSchemaDebug() {
  window.__NODE_SCHEMA_DEBUG = window.__NODE_SCHEMA_DEBUG || {
    history: [],
    logAccess: function(node) {
      if (!node || !node.data || !node.data.configSchema) return;
      this.history.push({
        timestamp: new Date().toISOString(),
        nodeId: node.id,
        nodeType: node.type,
        schemaId: node.data.configSchema.nodeId,
        schemaTitle: node.data.configSchema.title,
        schemaProps: node.data.configSchema.properties ? Object.keys(node.data.configSchema.properties) : []
      });
      console.log(`[NODE-DEBUG] Schema access registered: ${node.type} -> ${node.data.configSchema.nodeId || 'NO-ID'}`);
    },
    showHistory: function() {
      console.log(`\n[NODE-DEBUG] === SCHEMA HISTORY (${this.history.length} entries) ===`);
      this.history.forEach((entry, i) => {
        console.log(`[NODE-DEBUG] ${i+1}. ${entry.timestamp} - Node: ${entry.nodeType} -> Schema: ${entry.schemaId}`);
        console.log(`[NODE-DEBUG]    Properties: ${entry.schemaProps.join(', ')}`);
      });
    }
  };
  window.showSchemaHistory = function() {
    window.__NODE_SCHEMA_DEBUG.showHistory();
  };
  console.log(`[NODE-DEBUG] SchemaDebugTools loaded. Use window.showSchemaHistory() to see schema history.`);
}
