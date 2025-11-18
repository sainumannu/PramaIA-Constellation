import api from './api';

class GroupService {
  // GET - Ottiene tutti i gruppi
  async getAllGroups(skip = 0, limit = 100, isActive = null) {
    try {
      const params = new URLSearchParams({
        skip: skip.toString(),
        limit: limit.toString()
      });
      
      if (isActive !== null) {
        params.append('is_active', isActive.toString());
      }
      
      const response = await api.get(`/api/groups?${params}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nel recupero dei gruppi');
    }
  }

  // GET - Ottiene un gruppo specifico
  async getGroup(groupId) {
    try {
      const response = await api.get(`/api/groups/${groupId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nel recupero del gruppo');
    }
  }

  // POST - Crea un nuovo gruppo
  async createGroup(groupData) {
    try {
      const response = await api.post('/api/groups', groupData);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nella creazione del gruppo');
    }
  }

  // PUT - Aggiorna un gruppo esistente
  async updateGroup(groupId, groupData) {
    try {
      const response = await api.put(`/api/groups/${groupId}`, groupData);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nell\'aggiornamento del gruppo');
    }
  }

  // DELETE - Elimina un gruppo
  async deleteGroup(groupId) {
    try {
      const response = await api.delete(`/api/groups/${groupId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nell\'eliminazione del gruppo');
    }
  }

  // POST - Aggiunge membri a un gruppo
  async addMembersToGroup(groupId, userIds, roleInGroup = 'member') {
    try {
      const response = await api.post(`/api/groups/${groupId}/members`, {
        user_ids: userIds,
        role_in_group: roleInGroup
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nell\'aggiunta dei membri al gruppo');
    }
  }

  // DELETE - Rimuove un membro da un gruppo
  async removeMemberFromGroup(groupId, userId) {
    try {
      const response = await api.delete(`/api/groups/${groupId}/members/${userId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nella rimozione del membro dal gruppo');
    }
  }

  // PUT - Aggiorna il ruolo di un membro nel gruppo
  async updateMemberRole(groupId, userId, newRole) {
    try {
      const response = await api.put(`/api/groups/${groupId}/members/${userId}`, {
        role_in_group: newRole
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nell\'aggiornamento del ruolo del membro');
    }
  }

  // GET - Ottiene i membri di un gruppo
  async getGroupMembers(groupId) {
    try {
      const response = await api.get(`/api/groups/${groupId}/members`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Errore nel recupero dei membri del gruppo');
    }
  }

  // Helper per gestire gli errori
  handleError(error, defaultMessage) {
    if (error.response) {
      // Errore dal server
      const message = error.response.data?.detail || error.response.data?.message || defaultMessage;
      return new Error(message);
    } else if (error.request) {
      // Errore di rete
      return new Error('Errore di connessione. Verifica che il backend sia avviato.');
    } else {
      // Altro errore
      return new Error(defaultMessage);
    }
  }
}

export default new GroupService();
