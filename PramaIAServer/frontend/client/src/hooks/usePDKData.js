/**
 * Custom React hook for PDK data management with tag support
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { PDK_SERVER_BASE_URL, API_BASE_URL } from '../config/appConfig';
import api from '../services/api';

export const usePDKData = () => {
  const [plugins, setPlugins] = useState([]);
  const [eventSources, setEventSources] = useState([]);
  const [tagStats, setTagStats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch plugins with tag support
  const fetchPlugins = useCallback(async (filters = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (filters.tags && filters.tags.length > 0) {
        params.append('tags', filters.tags.join(','));
      }
      if (filters.exclude_tags && filters.exclude_tags.length > 0) {
        params.append('exclude_tags', filters.exclude_tags.join(','));
      }
      if (filters.mode) {
        params.append('mode', filters.mode);
      }

      // Try PDK server first, fallback to main API
      let response;
      try {
        response = await fetch(`${PDK_SERVER_BASE_URL}/api/plugins?${params.toString()}`);
        if (!response.ok) throw new Error('PDK server not available');
        const data = await response.json();
        setPlugins(data.plugins || []);
      } catch (pdkError) {
        console.warn('PDK server not available, using main API:', pdkError);
        response = await api.get(`/api/pdk/plugins?${params.toString()}`);
        setPlugins(response.data || []);
      }
    } catch (err) {
      setError('Failed to fetch plugins: ' + err.message);
      setPlugins([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch event sources with tag support
  const fetchEventSources = useCallback(async (filters = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (filters.tags && filters.tags.length > 0) {
        params.append('tags', filters.tags.join(','));
      }
      if (filters.exclude_tags && filters.exclude_tags.length > 0) {
        params.append('exclude_tags', filters.exclude_tags.join(','));
      }
      if (filters.mode) {
        params.append('mode', filters.mode);
      }

      const response = await fetch(`${PDK_SERVER_BASE_URL}/api/event-sources?${params.toString()}`);
      if (!response.ok) throw new Error('Failed to fetch event sources');
      
      const data = await response.json();
      setEventSources(data || []);
    } catch (err) {
      setError('Failed to fetch event sources: ' + err.message);
      setEventSources([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch tag statistics
  const fetchTagStats = useCallback(async () => {
    try {
      const response = await fetch(`${PDK_SERVER_BASE_URL}/api/tags`);
      if (!response.ok) throw new Error('Failed to fetch tag stats');
      
      const data = await response.json();
      setTagStats(data.statistics || []);
    } catch (err) {
      console.warn('Failed to fetch tag stats:', err);
      setTagStats([]);
    }
  }, []);

  // Load initial data
  useEffect(() => {
    fetchPlugins();
    fetchEventSources();
    fetchTagStats();
  }, [fetchPlugins, fetchEventSources, fetchTagStats]);

  // Computed values
  const allItems = useMemo(() => [
    ...plugins.map(p => ({ ...p, type: 'plugin' })),
    ...eventSources.map(es => ({ ...es, type: 'event-source' }))
  ], [plugins, eventSources]);

  const allTags = useMemo(() => {
    const tagSet = new Set();
    allItems.forEach(item => {
      (item.tags || []).forEach(tag => tagSet.add(tag));
    });
    return Array.from(tagSet).sort();
  }, [allItems]);

  return {
    // Data
    plugins,
    eventSources,
    allItems,
    allTags,
    tagStats,
    
    // State
    loading,
    error,
    
    // Actions
    fetchPlugins,
    fetchEventSources,
    fetchTagStats,
    
    // Utilities
    refreshAll: useCallback(() => {
      fetchPlugins();
      fetchEventSources();
      fetchTagStats();
    }, [fetchPlugins, fetchEventSources, fetchTagStats])
  };
};

export const usePDKPlugins = (initialFilters = {}) => {
  const [plugins, setPlugins] = useState([]);
  const [filteredPlugins, setFilteredPlugins] = useState([]);
  const [filters, setFilters] = useState(initialFilters);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchPlugins = useCallback(async (currentFilters = filters) => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (currentFilters.tags && currentFilters.tags.length > 0) {
        params.append('tags', currentFilters.tags.join(','));
      }
      if (currentFilters.exclude_tags && currentFilters.exclude_tags.length > 0) {
        params.append('exclude_tags', currentFilters.exclude_tags.join(','));
      }
      if (currentFilters.mode) {
        params.append('mode', currentFilters.mode);
      }

      // Try PDK server first, fallback to main API
      let data;
      try {
        const response = await fetch(`${PDK_SERVER_BASE_URL}/api/plugins?${params.toString()}`);
        if (!response.ok) throw new Error('PDK server not available');
        const result = await response.json();
        data = result.plugins || [];
      } catch (pdkError) {
        console.warn('PDK server not available, using main API:', pdkError);
        const response = await api.get(`/api/pdk/plugins?${params.toString()}`);
        data = response.data || [];
      }

      // Filtra per mostrare solo i plugin veri (non event sources)
      const actualPlugins = data.filter(item => {
        // Esclude esplicitamente gli event sources
        return item.type !== 'event-source';
      });

      setPlugins(actualPlugins);
      setFilteredPlugins(actualPlugins);
    } catch (err) {
      setError('Failed to fetch plugins: ' + err.message);
      setPlugins([]);
      setFilteredPlugins([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const updateFilters = useCallback((newFilters) => {
    setFilters({ ...filters, ...newFilters });
    fetchPlugins({ ...filters, ...newFilters });
  }, [filters, fetchPlugins]);

  const applyLocalFilter = useCallback((filterFn) => {
    setFilteredPlugins(plugins.filter(filterFn));
  }, [plugins]);

  const resetFilters = useCallback(() => {
    setFilters(initialFilters);
    setFilteredPlugins(plugins);
  }, [initialFilters, plugins]);

  useEffect(() => {
    fetchPlugins();
  }, [fetchPlugins]);

  return {
    plugins: filteredPlugins,
    allPlugins: plugins,
    filters,
    loading,
    error,
    updateFilters,
    applyLocalFilter,
    resetFilters,
    refresh: () => fetchPlugins()
  };
};

export const usePDKEventSources = (initialFilters = {}) => {
  const [eventSources, setEventSources] = useState([]);
  const [filteredEventSources, setFilteredEventSources] = useState([]);
  const [filters, setFilters] = useState(initialFilters);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchEventSources = useCallback(async (currentFilters = filters) => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (currentFilters.tags && currentFilters.tags.length > 0) {
        params.append('tags', currentFilters.tags.join(','));
      }
      if (currentFilters.exclude_tags && currentFilters.exclude_tags.length > 0) {
        params.append('exclude_tags', currentFilters.exclude_tags.join(','));
      }
      if (currentFilters.mode) {
        params.append('mode', currentFilters.mode);
      }

      const response = await fetch(`${PDK_SERVER_BASE_URL}/api/event-sources?${params.toString()}`);
      if (!response.ok) throw new Error('Failed to fetch event sources');
      
      const data = await response.json();
      setEventSources(data || []);
      setFilteredEventSources(data || []);
    } catch (err) {
      setError('Failed to fetch event sources: ' + err.message);
      setEventSources([]);
      setFilteredEventSources([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const updateFilters = useCallback((newFilters) => {
    setFilters({ ...filters, ...newFilters });
    fetchEventSources({ ...filters, ...newFilters });
  }, [filters, fetchEventSources]);

  const applyLocalFilter = useCallback((filterFn) => {
    setFilteredEventSources(eventSources.filter(filterFn));
  }, [eventSources]);

  const resetFilters = useCallback(() => {
    setFilters(initialFilters);
    setFilteredEventSources(eventSources);
  }, [initialFilters, eventSources]);

  useEffect(() => {
    fetchEventSources();
  }, [fetchEventSources]);

  return {
    eventSources: filteredEventSources,
    allEventSources: eventSources,
    filters,
    loading,
    error,
    updateFilters,
    applyLocalFilter,
    resetFilters,
    refresh: () => fetchEventSources()
  };
};

export default usePDKData;
