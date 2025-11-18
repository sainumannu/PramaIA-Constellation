/**
 * Sistema di tracciamento per proprietà icon e color dei nodi
 * Simula getter/setter con logging completo
 */

class NodePropertyTracker {
    static wrapNodeWithTracking(node, nodeId = 'unknown') {
        if (node._isTracked) return node;

        // Salva i valori originali
        const originalIcon = node.data?.icon || '';
        const originalColor = node.data?.color || '#ffffff';

        // Crea oggetti interni per memorizzare i valori
        node._iconValue = originalIcon;
        node._colorValue = originalColor;
        node._isTracked = true;

        console.log(`🔍 [TRACKER] Inizializzazione nodo ${nodeId}:`, {
            type: node.type,
            originalIcon,
            originalColor,
            stackTrace: new Error().stack.split('\n').slice(1, 4).join('\n')
        });

        // Definisce getter/setter per data.icon
        if (!node.data) node.data = {};
        
        Object.defineProperty(node.data, 'icon', {
            get() {
                console.log(`📖 [TRACKER] GET icon per ${nodeId}: "${node._iconValue}"`, {
                    stack: new Error().stack.split('\n')[2]?.trim()
                });
                return node._iconValue;
            },
            set(newValue) {
                const oldValue = node._iconValue;
                node._iconValue = newValue;
                console.log(`✏️ [TRACKER] SET icon per ${nodeId}: "${oldValue}" → "${newValue}"`, {
                    stack: new Error().stack.split('\n')[2]?.trim(),
                    stackTrace: new Error().stack.split('\n').slice(1, 4).join('\n')
                });
            },
            enumerable: true,
            configurable: true
        });

        // Definisce getter/setter per data.color
        Object.defineProperty(node.data, 'color', {
            get() {
                console.log(`🎨 [TRACKER] GET color per ${nodeId}: "${node._colorValue}"`, {
                    stack: new Error().stack.split('\n')[2]?.trim()
                });
                return node._colorValue;
            },
            set(newValue) {
                const oldValue = node._colorValue;
                node._colorValue = newValue;
                console.log(`🎨 [TRACKER] SET color per ${nodeId}: "${oldValue}" → "${newValue}"`, {
                    stack: new Error().stack.split('\n')[2]?.trim(),
                    stackTrace: new Error().stack.split('\n').slice(1, 4).join('\n')
                });
            },
            enumerable: true,
            configurable: true
        });

        return node;
    }

    static wrapNodesArray(nodes) {
        return nodes.map((node, index) => 
            this.wrapNodeWithTracking(node, `${node.id || node.type}_${index}`)
        );
    }

    static logCurrentState(nodes, context = 'unknown') {
        console.log(`📊 [TRACKER] Stato corrente nodi (${context}):`);
        nodes.forEach((node, index) => {
            console.log(`  ${index + 1}. ${node.id || node.type}:`, {
                icon: node.data?.icon || 'undefined',
                color: node.data?.color || 'undefined',
                _iconValue: node._iconValue || 'undefined',
                _colorValue: node._colorValue || 'undefined'
            });
        });
    }
}

export default NodePropertyTracker;
