// Componente per un elemento nodo nella lista
import React, { useState } from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Button, 
  Box, 
  Chip,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import CategoryIcon from '@mui/icons-material/Category';
import NodeDetailsModal from './NodeDetailsModal';
import { determineNodeCategory } from '../utils/nodeCategories';
import { NODE_CATEGORIES } from '../config/appConfig';

/**
 * Componente che rappresenta un singolo nodo nella lista dei nodi
 */
const NodeItem = ({ node, plugin, categoryOverrides = {} }) => {
  const [detailsOpen, setDetailsOpen] = useState(false);
  
  // Determina la categoria del nodo
  const nodeId = plugin ? `${plugin.id}/${node.id}` : node.id;
  const overriddenCategory = categoryOverrides[nodeId];
  const computedCategory = determineNodeCategory(node, plugin);
  const nodeCategory = overriddenCategory || computedCategory;
  
  // Trova le informazioni della categoria
  const categoryInfo = NODE_CATEGORIES.find(c => c.value === nodeCategory) || { 
    label: nodeCategory, 
    description: 'Categoria personalizzata' 
  };
  
  // Gestisce l'apertura del modal dei dettagli
  const handleOpenDetails = () => {
    setDetailsOpen(true);
  };
  
  // Gestisce la chiusura del modal dei dettagli
  const handleCloseDetails = () => {
    setDetailsOpen(false);
  };
  
  return (
    <>
      <Card 
        variant="outlined" 
        sx={{ 
          mb: 1,
          transition: 'all 0.2s',
          '&:hover': {
            boxShadow: 2,
            transform: 'translateY(-2px)'
          }
        }}
      >
        <CardContent sx={{ pb: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <Typography variant="h6" component="h3" gutterBottom>
              {node.name}
            </Typography>
            
            <Tooltip title="Visualizza dettagli">
              <IconButton 
                size="small" 
                onClick={handleOpenDetails} 
                color="primary"
                aria-label="visualizza dettagli"
              >
                <InfoIcon />
              </IconButton>
            </Tooltip>
          </Box>
          
          {node.description && (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {node.description}
            </Typography>
          )}
          
          <Divider sx={{ my: 1 }} />
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <CategoryIcon fontSize="small" color="action" sx={{ mr: 0.5 }} />
              <Typography variant="body2" color="text.secondary">
                {categoryInfo.label}
              </Typography>
            </Box>
            
            <Box>
              <Chip 
                label={plugin ? 'PDK' : 'Core'} 
                size="small" 
                color={plugin ? 'secondary' : 'primary'} 
                variant="outlined"
              />
              
              {overriddenCategory && (
                <Chip 
                  label="Personalizzato" 
                  size="small" 
                  color="warning" 
                  variant="outlined"
                  sx={{ ml: 0.5 }}
                />
              )}
            </Box>
          </Box>
        </CardContent>
        
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', p: 1, pt: 0 }}>
          <Button 
            size="small" 
            onClick={handleOpenDetails}
            color="primary"
          >
            Dettagli
          </Button>
        </Box>
      </Card>
      
      <NodeDetailsModal 
        open={detailsOpen} 
        node={node} 
        plugin={plugin} 
        onClose={handleCloseDetails} 
      />
    </>
  );
};

export default NodeItem;
