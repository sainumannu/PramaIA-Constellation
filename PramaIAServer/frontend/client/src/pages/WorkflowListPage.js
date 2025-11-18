import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import workflowService from '../services/workflowService.js';
import toast from 'react-hot-toast';

const WorkflowCard = ({ workflow, onDelete, onDuplicate }) => {
  const navigate = useNavigate();
  
  // Log ogni renderizzazione del componente
  React.useEffect(() => {
    console.log(`🔄 Renderizzazione WorkflowCard: ${workflow.name} (ID: ${workflow.workflow_id})`);
    
    return () => {
      console.log(`🗑️ Smontaggio WorkflowCard: ${workflow.name} (ID: ${workflow.workflow_id})`);
    };
  }, [workflow.workflow_id, workflow.name]);
  
  const handleEdit = () => {
    console.log('[WorkflowCard] Edit clicked for workflow:', workflow);
    console.log('[WorkflowCard] workflow_id:', workflow.workflow_id);
    console.log('[WorkflowCard] Navigating to:', `/app/workflows/${workflow.workflow_id}`);
    navigate(`/app/workflows/${workflow.workflow_id}`);
  };

  const handleDelete = async () => {
    if (window.confirm(`Sei sicuro di voler eliminare il workflow "${workflow.name}"?`)) {
      try {
        await workflowService.deleteWorkflow(workflow.workflow_id);
        toast.success('Workflow eliminato con successo!');
        onDelete(workflow.workflow_id);
      } catch (error) {
        console.error('Error deleting workflow:', error);
        
        // Gestione specifica degli errori
        if (error.response?.status === 404) {
          toast.warning('Il workflow non esiste più nel sistema. Aggiornamento della lista...');
          // Il workflow non esiste nel backend, rimuoviamolo anche dal frontend
          onDelete(workflow.workflow_id);
        } else if (error.response?.status === 403) {
          toast.error('Non hai i permessi per eliminare questo workflow');
        } else {
          toast.error('Errore nell\'eliminazione del workflow');
        }
      }
    }
  };

  const handleDuplicate = async () => {
    try {
      const originalWorkflow = await workflowService.getWorkflow(workflow.workflow_id);
      
      const duplicateData = {
        name: `${workflow.name} (Copia)`,
        description: `Copia di: ${workflow.description || ''}`,
        is_active: originalWorkflow.is_active,
        is_public: originalWorkflow.is_public,
        assigned_groups: originalWorkflow.assigned_groups,
        nodes: originalWorkflow.nodes,
        connections: originalWorkflow.connections
      };
      
      await workflowService.createWorkflow(duplicateData);
      toast.success('Workflow duplicato con successo!');
      onDuplicate();
    } catch (error) {
      toast.error('Errore nella duplicazione del workflow');
      console.error('Error duplicating workflow:', error);
    }
  };

  const handleRename = async () => {
    const newName = prompt('Nuovo nome del workflow:', workflow.name);
    if (newName && newName.trim() && newName !== workflow.name) {
      try {
        await workflowService.updateWorkflow(workflow.workflow_id, {
          name: newName.trim()
        });
        toast.success('Workflow rinominato con successo!');
        onDuplicate(); // Refresh the list
      } catch (error) {
        toast.error('Errore nella rinomina del workflow');
        console.error('Error renaming workflow:', error);
      }
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-shadow duration-200">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              {workflow.name}
            </h3>
            <p className="text-sm text-gray-600 mb-2">
              {workflow.description || 'Nessuna descrizione'}
            </p>
          </div>
          
          {/* Status badges */}
          <div className="flex flex-col items-end space-y-1">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              workflow.is_active 
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-800'
            }`}>
              {workflow.is_active ? 'Attivo' : 'Inattivo'}
            </span>
            
            {workflow.is_public && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Pubblico
              </span>
            )}
          </div>
        </div>

        {/* Tags and Category */}
        {(workflow.tags || workflow.category) && (
          <div className="mb-4">
            <div className="flex items-center flex-wrap gap-2">
              {/* Category badge */}
              {workflow.category && (
                <span 
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium text-white"
                  style={{ backgroundColor: workflow.color || '#6B7280' }}
                >
                  📂 {workflow.category}
                </span>
              )}
              
              {/* Tag badges */}
              {workflow.tags && Array.isArray(workflow.tags) && workflow.tags.map((tag, index) => (
                <span 
                  key={index}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 border border-indigo-200"
                >
                  🏷️ {tag}
                </span>
              ))}
              
              {/* Tags from JSON string */}
              {workflow.tags && typeof workflow.tags === 'string' && (() => {
                try {
                  const parsedTags = JSON.parse(workflow.tags);
                  return Array.isArray(parsedTags) && parsedTags.map((tag, index) => (
                    <span 
                      key={index}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 border border-indigo-200"
                    >
                      🏷️ {tag}
                    </span>
                  ));
                } catch (e) {
                  return null;
                }
              })()}
            </div>
          </div>
        )}

        {/* Info */}
        <div className="grid grid-cols-2 gap-4 mb-4 text-sm text-gray-600">
          <div>
            <span className="font-medium">Nodi:</span> {workflow.nodes_count || 0}
          </div>
          <div>
            <span className="font-medium">Creato da:</span> {workflow.created_by}
          </div>
          <div>
            <span className="font-medium">Creato il:</span> {formatDate(workflow.created_at)}
          </div>
          <div>
            <span className="font-medium">Modificato il:</span> {formatDate(workflow.updated_at)}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <div className="flex space-x-1">
            <button
              onClick={handleEdit}
              className="inline-flex items-center px-3 py-2 border border-transparent text-xs font-medium rounded text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              <svg className="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Modifica
            </button>
            
            <button
              onClick={handleRename}
              className="inline-flex items-center p-2 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
              title="Rinomina workflow"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </button>
            
            <button
              onClick={handleDuplicate}
              className="inline-flex items-center p-2 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              title="Duplica workflow"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
          </div>
          
          <button
            onClick={handleDelete}
            className="inline-flex items-center p-2 border border-red-300 text-xs font-medium rounded text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
            title="Elimina workflow"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

const WorkflowListPage = () => {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterActive, setFilterActive] = useState('all');
  const [selectedTags, setSelectedTags] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const navigate = useNavigate();

  // Log del ciclo di vita del componente principale
  useEffect(() => {
    console.log('🔵 WorkflowListPage: Componente montato');
    
    return () => {
      console.log('🔴 WorkflowListPage: Componente smontato');
    };
  }, []);

  useEffect(() => {
    console.log('🔄 WorkflowListPage: Caricamento workflow iniziale');
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      console.log('🔄 Caricamento workflow dal database...');
      const data = await workflowService.getAllWorkflows();
      
      console.log('📊 Dati ricevuti dall\'API:', data);
      
      // Debug log per verificare duplicati
      const ids = data.map(w => w.workflow_id);
      const uniqueIds = [...new Set(ids)];
      
      if (ids.length !== uniqueIds.length) {
        console.error('❌ DUPLICATI RILEVATI DALL\'API:', {
          totalCount: ids.length,
          uniqueCount: uniqueIds.length,
          duplicateIds: ids.filter((id, index) => ids.indexOf(id) !== index),
          allData: data
        });
        
        // Filtra i duplicati lato client come workaround temporaneo
        const uniqueWorkflows = data.filter((workflow, index, self) => 
          index === self.findIndex(w => w.workflow_id === workflow.workflow_id)
        );
        
        console.log('🔧 Filtrati duplicati lato client:', uniqueWorkflows);
        setWorkflows(uniqueWorkflows);
      } else {
        console.log('✅ Nessun duplicato rilevato');
        setWorkflows(data);
      }
    } catch (error) {
      toast.error('Errore nel caricamento dei workflow');
      console.error('Error loading workflows:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = (workflowId) => {
    setWorkflows(workflows.filter(w => w.workflow_id !== workflowId));
  };

  const handleDuplicate = () => {
    loadWorkflows(); // Reload to show the new duplicate
  };

  // Helper functions for tags and categories
  const getAllTags = () => {
    const tagSet = new Set();
    workflows.forEach(workflow => {
      if (workflow.tags) {
        try {
          const tags = typeof workflow.tags === 'string' ? JSON.parse(workflow.tags) : workflow.tags;
          if (Array.isArray(tags)) {
            tags.forEach(tag => tagSet.add(tag));
          }
        } catch (e) {
          // Ignore parsing errors
        }
      }
    });
    return Array.from(tagSet).sort();
  };

  const getAllCategories = () => {
    const categorySet = new Set();
    workflows.forEach(workflow => {
      if (workflow.category && workflow.category.trim()) {
        categorySet.add(workflow.category);
      }
    });
    return Array.from(categorySet).sort();
  };

  const toggleTag = (tag) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const toggleCategory = (category) => {
    setSelectedCategories(prev => 
      prev.includes(category) 
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  const clearAllFilters = () => {
    setSelectedTags([]);
    setSelectedCategories([]);
    setFilterActive('all');
    setSearchTerm('');
  };

  // Enhanced filtering logic
  const filteredWorkflows = workflows.filter(workflow => {
    // Search filter
    const matchesSearch = workflow.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (workflow.description && workflow.description.toLowerCase().includes(searchTerm.toLowerCase()));
    
    // Active filter
    const matchesFilter = filterActive === 'all' || 
                         (filterActive === 'active' && workflow.is_active) ||
                         (filterActive === 'inactive' && !workflow.is_active);
    
    // Tag filter
    let matchesTags = true;
    if (selectedTags.length > 0) {
      let workflowTags = [];
      try {
        workflowTags = typeof workflow.tags === 'string' ? JSON.parse(workflow.tags) : workflow.tags || [];
      } catch (e) {
        workflowTags = [];
      }
      matchesTags = selectedTags.every(tag => workflowTags.includes(tag));
    }
    
    // Category filter
    let matchesCategories = true;
    if (selectedCategories.length > 0) {
      matchesCategories = selectedCategories.includes(workflow.category);
    }
    
    return matchesSearch && matchesFilter && matchesTags && matchesCategories;
  });

  // Log dello stato dei workflow ad ogni render
  useEffect(() => {
    console.log('📊 WorkflowListPage stato attuale:', {
      workflowCount: workflows.length,
      uniqueIds: [...new Set(workflows.map(w => w.workflow_id))].length,
      loading,
      filteredCount: filteredWorkflows.length
    });
  }, [workflows, loading, filteredWorkflows]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Caricamento workflow...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Gestione Workflow</h1>
              <p className="mt-2 text-gray-600">Gestisci i tuoi workflow visuali</p>
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={loadWorkflows}
                disabled={loading}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors disabled:opacity-50"
              >
                <svg className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                {loading ? 'Aggiornamento...' : 'Aggiorna'}
              </button>
              
              <Link
                to="/app/workflows/new"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Nuovo Workflow
              </Link>
            </div>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="mb-6 bg-white rounded-lg shadow p-4">
          <div className="flex flex-col gap-4">
            {/* Top row: Search and Status Filter */}
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search */}
              <div className="flex-1">
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <input
                    type="text"
                    placeholder="Cerca workflow..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              
              {/* Filter */}
              <div className="sm:w-48">
                <select
                  value={filterActive}
                  onChange={(e) => setFilterActive(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">Tutti i workflow</option>
                  <option value="active">Solo attivi</option>
                  <option value="inactive">Solo inattivi</option>
                </select>
              </div>

              {/* Clear Filters Button */}
              {(selectedTags.length > 0 || selectedCategories.length > 0 || filterActive !== 'all' || searchTerm) && (
                <button
                  onClick={clearAllFilters}
                  className="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors whitespace-nowrap"
                >
                  Pulisci Filtri
                </button>
              )}
            </div>

            {/* Second row: Tags and Categories */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Categories Filter */}
              {getAllCategories().length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    📂 Categorie ({selectedCategories.length} selezionate)
                  </label>
                  <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                    {getAllCategories().map(category => (
                      <button
                        key={category}
                        onClick={() => toggleCategory(category)}
                        className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                          selectedCategories.includes(category)
                            ? 'bg-blue-100 text-blue-800 border-2 border-blue-300'
                            : 'bg-gray-100 text-gray-700 border border-gray-300 hover:bg-gray-200'
                        }`}
                      >
                        {category} ({workflows.filter(w => w.category === category).length})
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Tags Filter */}
              {getAllTags().length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    🏷️ Tag ({selectedTags.length} selezionati)
                  </label>
                  <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                    {getAllTags().map(tag => (
                      <button
                        key={tag}
                        onClick={() => toggleTag(tag)}
                        className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                          selectedTags.includes(tag)
                            ? 'bg-indigo-100 text-indigo-800 border-2 border-indigo-300'
                            : 'bg-gray-100 text-gray-700 border border-gray-300 hover:bg-gray-200'
                        }`}
                      >
                        {tag} ({workflows.filter(w => {
                          try {
                            const tags = typeof w.tags === 'string' ? JSON.parse(w.tags) : w.tags || [];
                            return tags.includes(tag);
                          } catch (e) {
                            return false;
                          }
                        }).length})
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Active Filters Summary */}
            {(selectedTags.length > 0 || selectedCategories.length > 0) && (
              <div className="pt-2 border-t border-gray-200">
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Filtri attivi:</span>
                  <span className="ml-2">
                    {selectedCategories.length > 0 && `${selectedCategories.length} categorie`}
                    {selectedCategories.length > 0 && selectedTags.length > 0 && ', '}
                    {selectedTags.length > 0 && `${selectedTags.length} tag`}
                  </span>
                  <span className="ml-2 text-blue-600 font-medium">
                    → {filteredWorkflows.length} workflow trovati
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-blue-600">{workflows.length}</div>
            <div className="text-sm text-gray-600">Totale Workflow</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-green-600">
              {workflows.filter(w => w.is_active).length}
            </div>
            <div className="text-sm text-gray-600">Attivi</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-yellow-600">
              {workflows.filter(w => !w.is_active).length}
            </div>
            <div className="text-sm text-gray-600">Inattivi</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-purple-600">
              {workflows.filter(w => w.is_public).length}
            </div>
            <div className="text-sm text-gray-600">Pubblici</div>
          </div>
        </div>

        {/* Workflow Grid */}
        {filteredWorkflows.length === 0 ? (
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">Nessun workflow trovato</h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm ? 'Prova a modificare i termini di ricerca.' : 'Inizia creando il tuo primo workflow.'}
            </p>
            {!searchTerm && (
              <div className="mt-6">
                <Link
                  to="/app/workflows/new"
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Crea Workflow
                </Link>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredWorkflows.map((workflow) => {
              console.log(`📋 Renderizzazione workflow nella lista: ${workflow.name} (ID: ${workflow.workflow_id})`);
              return (
                <WorkflowCard
                  key={workflow.workflow_id}
                  workflow={workflow}
                  onDelete={handleDelete}
                  onDuplicate={handleDuplicate}
                />
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowListPage;
