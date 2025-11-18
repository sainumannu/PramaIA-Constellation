import { useState, useEffect, useRef } from 'react';

/**
 * Hook personalizzato per gestire il layout responsive del WorkflowWidget
 * Adatta automaticamente il layout in base alla larghezza disponibile
 */
export const useWidgetLayout = () => {
  const [isCompact, setIsCompact] = useState(false);
  const [isUltraCompact, setIsUltraCompact] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const width = containerRef.current.offsetWidth;
        
        // Ultra compatto per larghezze molto piccole
        if (width < 280) {
          setIsUltraCompact(true);
          setIsCompact(true);
        }
        // Compatto per larghezze piccole
        else if (width < 350) {
          setIsUltraCompact(false);
          setIsCompact(true);
        }
        // Layout normale
        else {
          setIsUltraCompact(false);
          setIsCompact(false);
        }
      }
    };

    // Esegui al mount
    handleResize();

    // Observer per le modifiche di dimensione
    const resizeObserver = new ResizeObserver(handleResize);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    // Listener per il resize della finestra
    window.addEventListener('resize', handleResize);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  // Classi CSS dinamiche basate sulla larghezza
  const getLayoutClasses = () => {
    if (isUltraCompact) {
      return {
        container: 'bg-white rounded shadow p-2 w-full max-w-full overflow-hidden',
        header: 'flex items-center justify-between mb-2',
        title: 'text-base font-semibold truncate pr-1 flex-1 min-w-0',
        link: 'text-blue-600 hover:text-blue-800 text-xs whitespace-nowrap flex-shrink-0',
        list: 'space-y-1 max-h-48 overflow-y-auto',
        item: 'bg-gray-50 rounded p-1',
        itemHeader: 'flex items-center justify-between',
        itemTitle: 'font-medium text-xs truncate',
        itemDescription: 'text-xs text-gray-500 truncate mt-0.5',
        actions: 'flex items-center space-x-0.5 flex-shrink-0',
        badge: 'text-xs text-green-600 bg-green-100 px-1 py-0.5 rounded font-medium',
        button: 'text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded px-0.5 py-0.5 text-xs transition-colors',
        executionItem: 'bg-gray-50 rounded p-1 border-l-2 border-gray-300',
        executionActions: 'flex items-center space-x-0.5 flex-shrink-0',
        sectionDivider: 'mt-3 pt-2 border-t'
      };
    } else if (isCompact) {
      return {
        container: 'bg-white rounded-lg shadow p-3 w-full max-w-full overflow-hidden',
        header: 'flex items-center justify-between mb-3',
        title: 'text-lg font-semibold truncate pr-1 flex-1 min-w-0',
        link: 'text-blue-600 hover:text-blue-800 text-sm whitespace-nowrap flex-shrink-0',
        list: 'space-y-1.5 max-h-56 overflow-y-auto',
        item: 'bg-gray-50 rounded p-1.5',
        itemHeader: 'flex items-center justify-between',
        itemTitle: 'font-medium text-sm truncate',
        itemDescription: 'text-xs text-gray-500 truncate mt-0.5',
        actions: 'flex items-center space-x-1 flex-shrink-0',
        badge: 'text-xs text-green-600 bg-green-100 px-1.5 py-0.5 rounded font-medium',
        button: 'text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded px-1 py-0.5 text-sm transition-colors',
        executionItem: 'bg-gray-50 rounded p-1.5 border-l-2 border-gray-300',
        executionActions: 'flex items-center space-x-1 flex-shrink-0',
        sectionDivider: 'mt-4 pt-3 border-t'
      };
    } else {
      return {
        container: 'bg-white rounded-lg shadow p-4 w-full max-w-full overflow-hidden',
        header: 'flex items-center justify-between mb-4',
        title: 'text-lg font-semibold truncate pr-2 flex-1 min-w-0',
        link: 'text-blue-600 hover:text-blue-800 text-sm whitespace-nowrap flex-shrink-0',
        list: 'space-y-1.5 max-h-60 overflow-y-auto',
        item: 'bg-gray-50 rounded p-1.5',
        itemHeader: 'flex items-center justify-between',
        itemTitle: 'font-medium text-sm truncate',
        itemDescription: 'text-xs text-gray-500 truncate mt-0.5',
        actions: 'flex items-center space-x-1 flex-shrink-0',
        badge: 'text-xs text-green-600 bg-green-100 px-1.5 py-0.5 rounded font-medium',
        button: 'text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded px-1 py-0.5 text-sm transition-colors',
        executionItem: 'bg-gray-50 rounded p-1.5 border-l-2 border-gray-300',
        executionActions: 'flex items-center space-x-1 flex-shrink-0',
        sectionDivider: 'mt-6 pt-4 border-t'
      };
    }
  };

  return {
    containerRef,
    isCompact,
    isUltraCompact,
    classes: getLayoutClasses()
  };
};

export default useWidgetLayout;
