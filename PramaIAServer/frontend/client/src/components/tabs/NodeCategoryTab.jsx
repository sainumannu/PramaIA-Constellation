import React from 'react';
import {
  Box,
  Text,
  Divider,
  List,
  ListItem,
  FormControl,
  FormLabel,
  Select,
  Button,
  Flex,
  Code
} from "@chakra-ui/react";
import { NODE_CATEGORIES } from '../../config/appConfig';
import { saveCategoryOverride, resetCategoryOverride } from '../../utils/nodeCategories';

/**
 * Componente per il tab Categoria del NodeDetailsModal
 */
const NodeCategoryTab = ({ 
  node, 
  plugin, 
  nodeFullId, 
  nodeCategory, 
  categoryInfo, 
  categoryOverrides, 
  setCategoryOverrides,
  selectedCategory,
  setSelectedCategory,
  savingCategory,
  setSavingCategory,
  toast
}) => {
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
    <Box borderWidth="1px" borderRadius="md" p={4} bg="white">
      <Text fontWeight="bold" fontSize="lg" mb={4} color="blue.600">Categoria del nodo</Text>
    
      <Box p={4} bg="gray.50" borderRadius="md" mb={4} borderWidth="1px">
        <Text fontWeight="bold" fontSize="lg" mb={2}>
          {categoryInfo.label}
        </Text>
        
        <Text color="gray.600" mb={3}>
          {categoryInfo.description}
        </Text>
        
        <Divider my={2} />
        
        <Text fontSize="xs" color="gray.500">
          Valore interno: <Code>{nodeCategory}</Code>
        </Text>
      </Box>
      
      <Text fontWeight="semibold" fontSize="sm" mb={2}>
        Come viene determinata la categoria
      </Text>
      
      <List spacing={2} mb={6}>
        {categoryOverrides[nodeFullId] && (
          <ListItem>
            <Text fontWeight="medium">Sovrascrittura amministratore</Text>
            <Text fontSize="sm">La categoria è stata sovrascritta manualmente a "{nodeCategory}"</Text>
          </ListItem>
        )}
        {!categoryOverrides[nodeFullId] && node.category && (
          <ListItem>
            <Text fontWeight="medium">Categoria esplicita</Text>
            <Text fontSize="sm">Il nodo specifica esplicitamente la categoria "{node.category}"</Text>
          </ListItem>
        )}
        
        {!categoryOverrides[nodeFullId] && !node.category && node.tags && node.tags.length > 0 && (
          <ListItem>
            <Text fontWeight="medium">Inferita dai tag</Text>
            <Text fontSize="sm">La categoria è stata inferita dai tag del nodo: {node.tags.join(', ')}</Text>
          </ListItem>
        )}
        
        {!categoryOverrides[nodeFullId] && !node.category && plugin && plugin.category && (
          <ListItem>
            <Text fontWeight="medium">Categoria del plugin</Text>
            <Text fontSize="sm">Ereditata dalla categoria del plugin: "{plugin.category}"</Text>
          </ListItem>
        )}
        
        {!categoryOverrides[nodeFullId] && !node.category && (!node.tags || node.tags.length === 0) && (!plugin || !plugin.category) && (
          <ListItem>
            <Text fontWeight="medium">Categoria predefinita</Text>
            <Text fontSize="sm">Viene utilizzata la categoria predefinita "utility"</Text>
          </ListItem>
        )}
      </List>
      
      <Divider my={4} />
      
      <Text fontWeight="bold" fontSize="md" mb={3} color="blue.600">
        Modifica categoria
      </Text>
      
      <FormControl mb={4}>
        <FormLabel fontWeight="medium">Scegli una nuova categoria per questo nodo:</FormLabel>
        <Select 
          placeholder="Seleziona categoria" 
          value={selectedCategory} 
          onChange={(e) => setSelectedCategory(e.target.value)}
          bg="white"
          borderColor="gray.300"
          size="md"
        >
          {NODE_CATEGORIES.map(category => (
            <option key={category.value} value={category.value}>
              {category.label} - {category.description}
            </option>
          ))}
        </Select>
      </FormControl>
      
      <Flex gap={3}>
        <Button 
          colorScheme="blue" 
          onClick={handleSaveCategory}
          isDisabled={!selectedCategory || savingCategory}
          isLoading={savingCategory}
          size="md"
        >
          Salva categoria
        </Button>
        
        <Button 
          variant="outline"
          onClick={handleResetCategory}
          isDisabled={!categoryOverrides[nodeFullId] || savingCategory}
          isLoading={savingCategory}
          size="md"
        >
          Ripristina categoria predefinita
        </Button>
      </Flex>
    </Box>
  );
};

export default NodeCategoryTab;
