// Helper per correzioni e ricostruzioni di configSchema per nodi specifici

export function fixSchemaForNode(nodeType, schemaId, node) {
  // Restituisce true se ha applicato una correzione, false altrimenti
  if (!node || !node.data) return false;

  const baseType = (nodeType || '').toLowerCase();
  const sid = (schemaId || '').toLowerCase();

  // LLM processor è gestito altrove nel file principale. Qui gestiamo Event Logger
  if (baseType.includes('event') || baseType.includes('logger') || sid.includes('event')) {
    node.data.configSchema = {
      title: `Configurazione Event Logger`,
      type: 'object',
      nodeId: 'event_logger',
      nodeName: 'Event Logger',
      properties: {
        event_type: { type: 'string', title: 'Tipo evento', description: 'Tipo di evento da registrare', default: '' },
        file_name: { type: 'string', title: 'Nome file', description: "Nome del file coinvolto nell'evento", default: '' },
        status: { type: 'string', title: 'Stato', description: "Stato associato all'evento (es. success/failure)", default: '' },
        document_id: { type: ['string', 'null'], title: 'Document ID', description: 'ID del documento (opzionale)', default: null },
        metadata: { type: 'object', title: 'Metadati', description: 'Metadati aggiuntivi', default: {}, properties: {} },
        event_data: { type: 'object', title: 'Dati evento', description: "Dati arbitrari dell'evento", default: {}, properties: {} },
        event_source: { type: 'string', title: 'Sorgente evento', description: "Sorgente dell'evento", default: 'pdk_workflow' },
        user_id: { type: ['string', 'null'], title: 'User ID', description: 'ID utente (opzionale)', default: null },
        db_path: { type: 'string', title: 'Percorso DB', description: 'Percorso al DB dove registrare gli eventi', default: 'document_monitor_events.db' }
      }
    };

    if (!node.data.config) node.data.config = {};
    node.data.defaultConfig = node.data.defaultConfig || {};
    return true;
  }

  return false;
}
