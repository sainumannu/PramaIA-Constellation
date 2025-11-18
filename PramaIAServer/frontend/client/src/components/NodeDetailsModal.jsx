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

// Importo i componenti modulari
import NodeInfoTab from './tabs/NodeInfoTab';
import NodeCategoryTab from './tabs/NodeCategoryTab';
import NodeSchemaTab from './tabs/NodeSchemaTab';
import NodePluginTab from './tabs/NodePluginTab';
import NodeDebugTab from './tabs/NodeDebugTab';

// Importo le utilità e configurazioni necessarie
import { determineNodeCategory, loadCategoryOverrides } from '../utils/nodeCategories';
import { NODE_CATEGORIES } from '../config/appConfig';

/**
 * Componente Modal per visualizzare i dettagli di un nodo
 */
const NodeDetailsModal = ({ open, node, plugin, onClose }) => {
  
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
  
  // Gestisce il cambio di tab
  const handleTabChange = (index) => {
    setActiveTab(index);
    
    // Imposta una categoria selezionata di default quando si seleziona la scheda Categoria
    if (index === 1 && !selectedCategory) {
      setSelectedCategory(nodeCategory);
    }
  };
  
  return (
    <Modal isOpen={open} onClose={onClose} size="xl" closeOnOverlayClick={false}>
      <ModalOverlay bg="blackAlpha.600" />
      <ModalContent maxW="90vw" maxH="90vh">
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
                  node={node} 
                  plugin={plugin} 
                  nodeFullId={nodeFullId} 
                  nodeCategory={nodeCategory} 
                  categoryInfo={categoryInfo} 
                  categoryOverrides={categoryOverrides} 
                  setCategoryOverrides={setCategoryOverrides}
                  selectedCategory={selectedCategory}
                  setSelectedCategory={setSelectedCategory}
                  savingCategory={savingCategory}
                  setSavingCategory={setSavingCategory}
                  toast={toast}
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
                    isEventSource={isEventSource} 
                    pluginDetails={pluginDetails}
                    setPluginDetails={setPluginDetails}
                    loading={loading}
                    setLoading={setLoading}
                    error={error}
                    setError={setError}
                    activeTab={activeTab}
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
