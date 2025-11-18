import axios from 'axios';
import config from '../config';

const API_BASE_URL = config.BACKEND_URL;

class WorkflowService {
  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Interceptor per aggiungere automaticamente il token
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Interceptor per gestire errori comuni
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // WORKFLOW CRUD
  async getAllWorkflows() {
    try {
      const response = await this.api.get('/api/workflows/');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nel caricamento dei workflow');
    }
  }

  async getWorkflow(workflowId) {
    try {
      console.log('[WorkflowService] Getting workflow with ID:', workflowId);
      console.log('[WorkflowService] URL will be:', `/api/workflows/${workflowId}`);
      const response = await this.api.get(`/api/workflows/${workflowId}`);
      console.log('[WorkflowService] Response received:', response.data);
      console.log('🔍 [WORKFLOWSERVICE] getWorkflow - First node from backend:', response.data?.nodes?.[0]);
      if (response.data?.nodes?.[0]) {
        console.log('🔍 [WORKFLOWSERVICE] First node details:', {
          node_id: response.data.nodes[0].node_id,
          node_type: response.data.nodes[0].node_type,
          has_icon_in_config: !!response.data.nodes[0].node_config?.icon,
          icon_in_config: response.data.nodes[0].node_config?.icon,
          has_color_in_config: !!response.data.nodes[0].node_config?.color,
          color_in_config: response.data.nodes[0].node_config?.color
        });
      }
      return response.data;
    } catch (error) {
      console.error('[WorkflowService] Error getting workflow:', error);
      console.error('[WorkflowService] Error response:', error.response);
      throw this.handleError(error, 'Errore nel caricamento del workflow');
    }
  }

  async createWorkflow(workflowData) {
    try {
      console.log('🔍 [WORKFLOWSERVICE] createWorkflow - Sending data to backend:', workflowData);
      console.log('🔍 [WORKFLOWSERVICE] First node being sent:', workflowData.nodes?.[0]);
      const response = await this.api.post('/api/workflows/', workflowData);
      console.log('🔍 [WORKFLOWSERVICE] createWorkflow - Response from backend:', response.data);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nella creazione del workflow');
    }
  }

  async updateWorkflow(workflowId, workflowData) {
    try {
      console.log('🔍 [WORKFLOWSERVICE] updateWorkflow - Sending data to backend:', workflowData);
      console.log('🔍 [WORKFLOWSERVICE] First node being updated:', workflowData.nodes?.[0]);
      const response = await this.api.put(`/api/workflows/${workflowId}`, workflowData);
      console.log('🔍 [WORKFLOWSERVICE] updateWorkflow - Response from backend:', response.data);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nell\'aggiornamento del workflow');
    }
  }

  async deleteWorkflow(workflowId) {
    try {
      await this.api.delete(`/api/workflows/${workflowId}`);
      return true;
    } catch (error) {
      throw this.handleError(error, 'Errore nell\'eliminazione del workflow');
    }
  }

  // WORKFLOW EXECUTION
  async executeWorkflow(workflowId, executionData = {}) {
    try {
      const response = await this.api.post(
        `/api/workflows/${workflowId}/execute`,
        executionData
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nell\'esecuzione del workflow');
    }
  }

  async getExecutionStatus(executionId) {
    try {
      const response = await this.api.get(`/api/executions/${executionId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nel recupero dello stato di esecuzione');
    }
  }

  async getRecentExecutions(limit = 10) {
    try {
      const response = await this.api.get(`/api/workflows/executions/recent?limit=${limit}`);
      return response.data.executions || [];
    } catch (error) {
      throw this.handleError(error, 'Errore nel recupero delle esecuzioni recenti');
    }
  }

  // WORKFLOW ASSIGNMENTS (solo admin)
  async assignWorkflowToUser(workflowId, userId, permissions = {}) {
    try {
      const response = await this.api.post(`/api/workflows/${workflowId}/assign/user`, {
        user_id: userId,
        permissions: {
          can_execute: permissions.can_execute || true,
          can_modify: permissions.can_modify || false,
          can_share: permissions.can_share || false
        }
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nell\'assegnazione workflow all\'utente');
    }
  }

  async assignWorkflowToGroup(workflowId, groupName, permissions = {}) {
    try {
      const response = await this.api.post(`/api/workflows/${workflowId}/assign/group`, {
        group_name: groupName,
        permissions: {
          can_execute: permissions.can_execute || true,
          can_modify: permissions.can_modify || false,
          can_share: permissions.can_share || false
        }
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nell\'assegnazione workflow al gruppo');
    }
  }

  async getUsersForAssignment() {
    try {
      const response = await this.api.get('/api/workflows/users');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nel recupero degli utenti');
    }
  }

  // VALIDATION
  async validateWorkflow(workflowData) {
    try {
      const response = await this.api.post('/api/workflows/validate', workflowData);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nella validazione del workflow');
    }
  }

  // CONVERSIONE DATI
  convertToBackendFormat(nodes, edges, workflowInfo) {
    console.log('🔍 [WORKFLOWSERVICE] convertToBackendFormat - Input nodes:', nodes);
    console.log('🔍 [WORKFLOWSERVICE] Input nodes detailed:');
    nodes.forEach((node, index) => {
      console.log(`  Node ${index + 1}:`, {
        id: node.id,
        type: node.type,
        hasIcon: !!node.data?.icon,
        icon: node.data?.icon,
        hasColor: !!node.data?.color,
        color: node.data?.color,
        fullData: node.data
      });
    });

    const workflowData = {
      name: workflowInfo.name || 'Unnamed Workflow',
      description: workflowInfo.description || '',
      config: {
        reactFlow: {
          nodes: nodes,
          edges: edges,
          viewport: workflowInfo.viewport || { x: 0, y: 0, zoom: 1 }
        }
      },
      nodes: nodes.map(node => {
        const mappedNode = {
          node_id: node.id,
          node_type: node.type,
          node_config: {
            ...node.data,
            position: node.position
          },
          position_x: node.position.x,
          position_y: node.position.y
        };
        
        console.log(`🔍 [WORKFLOWSERVICE] Mapped node ${node.id}:`, {
          original_icon: node.data?.icon,
          original_color: node.data?.color,
          mapped_icon: mappedNode.node_config.icon,
          mapped_color: mappedNode.node_config.color,
          full_node_config: mappedNode.node_config
        });
        
        return mappedNode;
      }),
      connections: edges.map(edge => ({
        connection_id: edge.id,
        source_node_id: edge.source,
        target_node_id: edge.target,
        source_handle: edge.sourceHandle || 'output',
        target_handle: edge.targetHandle || 'input'
      }))
    };

    console.log('🔍 [WORKFLOWSERVICE] Final workflowData being sent to backend:');
    console.log('  Nodes in workflowData:', workflowData.nodes.length);
    workflowData.nodes.forEach((node, index) => {
      console.log(`  Backend Node ${index + 1}:`, {
        node_id: node.node_id,
        node_type: node.node_type,
        has_icon_in_config: !!node.node_config?.icon,
        icon_in_config: node.node_config?.icon,
        has_color_in_config: !!node.node_config?.color,
        color_in_config: node.node_config?.color,
        full_node_config_keys: Object.keys(node.node_config || {})
      });
    });

    return workflowData;
  }

  convertFromBackendFormat(workflowData) {
    console.log('🔍 [WORKFLOWSERVICE] convertFromBackendFormat - Raw data from backend:', workflowData);
    
    if (!workflowData) return { nodes: [], edges: [], workflowInfo: {} };

    console.log('🔍 [WORKFLOWSERVICE] Backend nodes received:', workflowData.nodes?.length || 0);
    workflowData.nodes?.forEach((node, index) => {
      console.log(`  Backend Node ${index + 1} received:`, {
        node_id: node.node_id,
        node_type: node.node_type,
        has_icon_in_config: !!node.node_config?.icon,
        icon_in_config: node.node_config?.icon,
        has_color_in_config: !!node.node_config?.color,
        color_in_config: node.node_config?.color,
        full_node_config: node.node_config
      });
    });

    const nodes = workflowData.nodes?.map(node => {
      const convertedNode = {
        id: node.node_id,
        type: node.node_type,
        position: {
          x: node.position_x || 0,
          y: node.position_y || 0
        },
        data: {
          ...node.node_config,
          label: node.node_config?.label || node.node_type
        }
      };
      
      console.log(`🔍 [WORKFLOWSERVICE] Converted node ${node.node_id}:`, {
        original_icon: node.node_config?.icon,
        original_color: node.node_config?.color,
        converted_icon: convertedNode.data.icon,
        converted_color: convertedNode.data.color,
        full_converted_data: convertedNode.data
      });
      
      return convertedNode;
    }) || [];

    const edges = workflowData.connections?.map(conn => ({
      id: conn.connection_id,
      source: conn.source_node_id,
      target: conn.target_node_id,
      sourceHandle: conn.source_handle,
      targetHandle: conn.target_handle,
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#4F46E5', strokeWidth: 2 }
    })) || [];

    const workflowInfo = {
      name: workflowData.name,
      description: workflowData.description,
      viewport: workflowData.config?.reactFlow?.viewport || { x: 0, y: 0, zoom: 1 },
      workflow_id: workflowData.workflow_id,
      created_at: workflowData.created_at,
      updated_at: workflowData.updated_at
    };

    console.log('🔍 [WORKFLOWSERVICE] Final converted result:');
    console.log('  Final nodes count:', nodes.length);
    nodes.forEach((node, index) => {
      console.log(`  Final Node ${index + 1}:`, {
        id: node.id,
        type: node.type,
        has_final_icon: !!node.data?.icon,
        final_icon: node.data?.icon,
        has_final_color: !!node.data?.color,
        final_color: node.data?.color,
        full_final_data_keys: Object.keys(node.data || {})
      });
    });

    return { nodes, edges, workflowInfo };
  }

  // ERROR HANDLING
  handleError(error, defaultMessage) {
    console.error('WorkflowService Error:', error);
    
    if (error.response?.data?.detail) {
      return new Error(error.response.data.detail);
    }
    
    if (error.response?.data?.message) {
      return new Error(error.response.data.message);
    }
    
    if (error.message) {
      return new Error(error.message);
    }
    
    return new Error(defaultMessage);
  }

  // WORKFLOW INPUT NODES
  async getWorkflowInputNodes(workflowId) {
    try {
      console.log('[WorkflowService] Getting input nodes for workflow:', workflowId);
      // Usa l'endpoint originale del workflow_router (ora corretto)
      const response = await this.api.get(`/api/workflows/${workflowId}/input-nodes`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nel caricamento dei nodi di input del workflow');
    }
  }
}

// Singleton instance
const workflowService = new WorkflowService();
export default workflowService;
