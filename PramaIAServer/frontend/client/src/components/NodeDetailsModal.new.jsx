import React, { useState, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useToast
} from "@chakra-ui/react";
import { determineNodeCategory, saveCategoryOverride, resetCategoryOverride, loadCategoryOverrides } from '../utils/nodeCategories';
import { NODE_CATEGORIES, PDK_PLUGINS_URL, PDK_EVENT_SOURCES_URL, PDK_BACKEND_PLUGINS_URL, PDK_BACKEND_EVENT_SOURCES_URL } from '../config/appConfig';

// Importazione dei componenti delle schede
import NodeInfoTab from './NodeInfoTab';
import NodeCategoryTab from './NodeCategoryTab';
import NodeSchemaTab from './NodeSchemaTab';
import NodePluginTab from './NodePluginTab';
import NodeDebugTab from './NodeDebugTab';

/**
 * Componente Modal per visualizzare i dettagli di un nodo
 */
const NodeDetailsModal = ({ open, node, plugin, onClose }) => {
  console.log("NodeDetailsModal rendering:", { open, node, plugin, NODE_CATEGORIES });
  
  const [activeTab, setActiveTab] = useState(0);
  const [pluginDetails, setPluginDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [categoryOverrides, setCategoryOverrides] = useState({});
  const [selectedCategory, setSelectedCategory] = useState('');
  const [savingCategory, setSavingCategory] = useState(false);
  const toast = useToast();
  
  // Carica le sovrascritture di categoria quando il modale viene aperto
  useEffect(() => {
    if (open) {
      loadCategoryOverrides()
        .then(overrides => {
          setCategoryOverrides(overrides);
        })
        .catch(err => {
          console.error('Errore nel caricamento delle sovrascritture:', err);
        });
    }
  }, [open]);
  
  if (!node) {
    return null;
  }
  
  // Genera l'ID completo del nodo (con plugin)
  const getNodeFullId = () => {
    return plugin ? `${plugin.id}/${node.id}` : node.id;
  };
  
  // Determina la categoria del nodo
  const nodeFullId = getNodeFullId();
  const nodeCategory = determineNodeCategory(node, plugin, categoryOverrides);
  const categoryInfo = NODE_CATEGORIES.find(c => c.value === nodeCategory) || { label: nodeCategory, description: '' };
  
  // Determina se è un event source
  const isEventSource = plugin?.type === 'event-source' || 
                        plugin?.eventTypes?.length > 0 || 
                        node.type === 'event-source';
  
  // Carica i dettagli del plugin manualmente quando si seleziona la scheda
  const loadPluginDetails = async () => {
    if (!plugin || !plugin.id) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Prova diverse possibili URL fino a trovarne una che funziona
      const possibleUrls = [
        `${PDK_PLUGINS_URL}/${plugin.id}`,
        `${PDK_EVENT_SOURCES_URL}/${plugin.id}`,
        `${PDK_BACKEND_PLUGINS_URL}/${plugin.id}`,
        `${PDK_BACKEND_EVENT_SOURCES_URL}/${plugin.id}`
      ];
      
      let response = null;
      let successUrl = null;
      
      for (const url of possibleUrls) {
        try {
          console.log(`Tentativo di caricamento da: ${url}`);
          const res = await fetch(url);
          if (res.ok) {
            response = await res.json();
            successUrl = url;
            break;
          }
        } catch (err) {
          console.log(`Errore caricamento da ${url}:`, err);
          // Continua con il prossimo URL
        }
      }
      
      if (response) {
        console.log(`Dati caricati con successo da: ${successUrl}`, response);
        setPluginDetails(response);
      } else {
        setError('Non è stato possibile caricare i dettagli del plugin da nessuno degli URL provati.');
      }
    } catch (err) {
      console.error('Errore nel caricamento dei dettagli del plugin:', err);
      setError(`Errore: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  // Gestisce il cambio di tab
  const handleTabChange = (index) => {
    console.log("Cambiando tab a:", index);
    setActiveTab(index);
    
    // Carica i dettagli del plugin quando si seleziona la scheda Plugin
    if (index === 3 && plugin && !pluginDetails && !loading) {
      loadPluginDetails();
    }
    
    // Imposta una categoria selezionata di default quando si seleziona la scheda Categoria
    if (index === 1 && !selectedCategory) {
      setSelectedCategory(nodeCategory);
    }
  };
  
  // Gestisce il salvataggio della categoria
  const handleSaveCategory = async () => {
    if (!selectedCategory) return;
    
    setSavingCategory(true);
    
    try {
      const success = await saveCategoryOverride(nodeFullId, selectedCategory);
      
      if (success) {
        // Aggiorna le sovrascritture locali
        setCategoryOverrides(prev => ({
          ...prev,
          [nodeFullId]: selectedCategory
        }));
        
        toast({
          title: "Categoria salvata",
          description: `La categoria del nodo è stata aggiornata a "${NODE_CATEGORIES.find(c => c.value === selectedCategory)?.label || selectedCategory}"`,
          status: "success",
          duration: 5000,
          isClosable: true,
        });
      } else {
        toast({
          title: "Errore",
          description: "Non è stato possibile salvare la categoria del nodo",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      }
    } catch (err) {
      console.error('Errore nel salvataggio della categoria:', err);
      toast({
        title: "Errore",
        description: "Si è verificato un errore durante il salvataggio della categoria",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setSavingCategory(false);
    }
  };
  
  // Gestisce il ripristino della categoria predefinita
  const handleResetCategory = async () => {
    setSavingCategory(true);
    
    try {
      const success = await resetCategoryOverride(nodeFullId);
      
      if (success) {
        // Rimuove la sovrascrittura locale
        const newOverrides = { ...categoryOverrides };
        delete newOverrides[nodeFullId];
        setCategoryOverrides(newOverrides);
        setSelectedCategory('');
        
        toast({
          title: "Categoria ripristinata",
          description: "La categoria del nodo è stata ripristinata al valore predefinito",
          status: "success",
          duration: 5000,
          isClosable: true,
        });
      } else {
        toast({
          title: "Errore",
          description: "Non è stato possibile ripristinare la categoria del nodo",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      }
    } catch (err) {
      console.error('Errore nel ripristino della categoria:', err);
      toast({
        title: "Errore",
        description: "Si è verificato un errore durante il ripristino della categoria",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setSavingCategory(false);
    }
  };
  
  return (
    <Modal isOpen={open} onClose={onClose} size="xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          {node.name}
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          <Tabs 
            isFitted 
            variant="line" 
            colorScheme="blue" 
            index={activeTab} 
            onChange={handleTabChange}
            mb="4"
          >
            <TabList mb="4">
              <Tab fontWeight="semibold" _selected={{ color: "blue.500", borderColor: "blue.500", borderBottom: "2px solid" }}>Informazioni</Tab>
              <Tab fontWeight="semibold" _selected={{ color: "blue.500", borderColor: "blue.500", borderBottom: "2px solid" }}>Categoria</Tab>
              {node.schema && <Tab fontWeight="semibold" _selected={{ color: "blue.500", borderColor: "blue.500", borderBottom: "2px solid" }}>Schema</Tab>}
              {plugin && <Tab fontWeight="semibold" _selected={{ color: "blue.500", borderColor: "blue.500", borderBottom: "2px solid" }}>Plugin</Tab>}
              <Tab fontWeight="semibold" _selected={{ color: "blue.500", borderColor: "blue.500", borderBottom: "2px solid" }}>Debug</Tab>
            </TabList>
            
            <TabPanels>
              {/* Pannello Informazioni */}
              <TabPanel>
                <NodeInfoTab 
                  node={node} 
                  plugin={plugin} 
                  isEventSource={isEventSource} 
                />
              </TabPanel>
              
              {/* Pannello Categoria */}
              <TabPanel>
                <NodeCategoryTab 
                  nodeCategory={nodeCategory}
                  categoryInfo={categoryInfo}
                  node={node}
                  plugin={plugin}
                  nodeFullId={nodeFullId}
                  categoryOverrides={categoryOverrides}
                  selectedCategory={selectedCategory}
                  setSelectedCategory={setSelectedCategory}
                  handleSaveCategory={handleSaveCategory}
                  handleResetCategory={handleResetCategory}
                  savingCategory={savingCategory}
                  NODE_CATEGORIES={NODE_CATEGORIES}
                />
              </TabPanel>
              
              {/* Pannello Schema */}
              {node.schema && (
                <TabPanel>
                  <NodeSchemaTab schema={node.schema} />
                </TabPanel>
              )}
              
              {/* Pannello Plugin */}
              {plugin && (
                <TabPanel>
                  <NodePluginTab 
                    plugin={plugin}
                    pluginDetails={pluginDetails}
                    loading={loading}
                    error={error}
                    isEventSource={isEventSource}
                    loadPluginDetails={loadPluginDetails}
                  />
                </TabPanel>
              )}
              
              {/* Pannello Debug */}
              <TabPanel>
                <NodeDebugTab />
              </TabPanel>
            </TabPanels>
          </Tabs>
        </ModalBody>
        
        <ModalFooter>
          <Button onClick={onClose}>
            Chiudi
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default NodeDetailsModal;
