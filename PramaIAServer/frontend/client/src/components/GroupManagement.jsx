import React, { useState, useEffect } from 'react';
import groupService from '../services/groupService';

const GroupManagement = () => {
  const [groups, setGroups] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);  // Aggiunto per modifica
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [showMembersModal, setShowMembersModal] = useState(false);

  // Form states
  const [newGroup, setNewGroup] = useState({
    name: '',
    description: '',
    color: '#3B82F6'
  });
  const [editGroup, setEditGroup] = useState({  // Aggiunto per modifica
    name: '',
    description: '',
    color: '#3B82F6'
  });
  const [selectedUsers, setSelectedUsers] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Carica gruppi usando il servizio
      const [groupsData, usersData] = await Promise.all([
        groupService.getAllGroups(),
        loadUsers()
      ]);
      
      setGroups(groupsData || []);
      setUsers(usersData || []);
    } catch (error) {
      console.error('Errore generale:', error);
      setMessage('Errore nel caricamento dei dati: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      // Usa il servizio workflow per ottenere gli utenti
      const workflowService = await import('../services/workflowService');
      return await workflowService.default.getUsersForAssignment();
    } catch (error) {
      console.error('Errore caricamento utenti:', error);
      // Fallback a dati mock
      return [
        { id: 'admin', email: 'admin@pramaia.com', role: 'admin' },
        { id: 'user1', email: 'user1@company.com', role: 'user' },
        { id: 'user2', email: 'user2@company.com', role: 'user' }
      ];
    }
  };

  const handleCreateGroup = async () => {
    if (!newGroup.name.trim()) {
      setMessage('Nome gruppo richiesto');
      return;
    }

    try {
      await groupService.createGroup(newGroup);
      setMessage('Gruppo creato con successo!');
      setShowCreateModal(false);
      setNewGroup({ name: '', description: '', color: '#3B82F6' });
      await loadData();
    } catch (error) {
      setMessage('Errore nella creazione del gruppo: ' + error.message);
    }
  };

  const handleEditGroup = (group) => {
    setSelectedGroup(group);
    setEditGroup({
      name: group.name,
      description: group.description || '',
      color: group.color || '#3B82F6'
    });
    setShowEditModal(true);
  };

  const handleUpdateGroup = async () => {
    if (!editGroup.name.trim()) {
      setMessage('Nome gruppo richiesto');
      return;
    }

    try {
      await groupService.updateGroup(selectedGroup.group_id, editGroup);
      setMessage('Gruppo aggiornato con successo!');
      setShowEditModal(false);
      setSelectedGroup(null);
      setEditGroup({ name: '', description: '', color: '#3B82F6' });
      await loadData();
    } catch (error) {
      setMessage('Errore nell\'aggiornamento del gruppo: ' + error.message);
    }
  };

  const handleDeleteGroup = async (groupId) => {
    if (!window.confirm('Sei sicuro di voler eliminare questo gruppo?')) return;

    try {
      await groupService.deleteGroup(groupId);
      setMessage('Gruppo eliminato con successo!');
      await loadData();
    } catch (error) {
      setMessage('Errore nell\'eliminazione del gruppo: ' + error.message);
    }
  };

  const handleAddMembersToGroup = async () => {
    if (selectedUsers.length === 0) {
      setMessage('Seleziona almeno un utente');
      return;
    }

    try {
      await groupService.addMembersToGroup(selectedGroup.group_id, selectedUsers);
      setMessage(`Aggiunti ${selectedUsers.length} membri al gruppo`);
      setShowMembersModal(false);
      setSelectedUsers([]);
      await loadData();
    } catch (error) {
      setMessage('Errore nell\'aggiunta membri: ' + error.message);
    }
  };

  const handleRemoveMember = async (groupId, userId) => {
    if (!window.confirm('Rimuovere questo utente dal gruppo?')) return;

    try {
      await groupService.removeMemberFromGroup(groupId, userId);
      setMessage('Membro rimosso dal gruppo');
      await loadData();
    } catch (error) {
      setMessage('Errore nella rimozione del membro: ' + error.message);
    }
  };

  const predefinedColors = [
    '#3B82F6', '#EF4444', '#10B981', '#F59E0B', 
    '#8B5CF6', '#F97316', '#06B6D4', '#84CC16'
  ];

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4 w-1/3"></div>
          <div className="space-y-3">
            <div className="h-6 bg-gray-200 rounded"></div>
            <div className="h-6 bg-gray-200 rounded"></div>
            <div className="h-6 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-blue-700">👥 Gestione Gruppi</h3>
        <div className="flex space-x-2">
          <button
            onClick={loadData}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
          >
            🔄 Aggiorna
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
          >
            ➕ Nuovo Gruppo
          </button>
        </div>
      </div>

      {message && (
        <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-4">
          {message}
          <button 
            onClick={() => setMessage('')}
            className="float-right text-blue-700 hover:text-blue-900"
          >
            ✕
          </button>
        </div>
      )}

      {groups.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500 mb-4">Nessun gruppo presente nel sistema</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg"
          >
            Crea il primo gruppo →
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {groups.map((group) => (
            <div 
              key={group.group_id} 
              className="bg-white rounded-lg shadow-md border hover:shadow-lg transition-shadow"
            >
              {/* Header del gruppo */}
              <div 
                className="p-4 rounded-t-lg text-white"
                style={{ backgroundColor: group.color }}
              >
                <h4 className="font-semibold text-lg">{group.name}</h4>
                <p className="text-sm opacity-90">
                  {group.description || 'Nessuna descrizione'}
                </p>
              </div>

              {/* Info del gruppo */}
              <div className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-sm text-gray-600">
                    <div>👤 Membri: <span className="font-medium">{group.members_count}</span></div>
                    <div>📅 Creato: <span className="text-xs">{new Date(group.created_at).toLocaleDateString()}</span></div>
                  </div>
                  <div className={`px-2 py-1 rounded text-xs ${
                    group.is_active 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {group.is_active ? '✅ Attivo' : '⏸️ Inattivo'}
                  </div>
                </div>

                {/* Lista membri (primi 3) */}
                {group.members && group.members.length > 0 && (
                  <div className="mb-3">
                    <div className="text-xs text-gray-500 mb-1">Membri:</div>
                    <div className="space-y-1">
                      {group.members.slice(0, 3).map((member, idx) => (
                        <div key={idx} className="flex items-center justify-between text-xs">
                          <span>{member.user_id}</span>
                          <span className="text-gray-400">{member.role_in_group}</span>
                        </div>
                      ))}
                      {group.members.length > 3 && (
                        <div className="text-xs text-gray-400">
                          +{group.members.length - 3} altri...
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Azioni */}
                <div className="flex space-x-2">
                  <button
                    onClick={() => {
                      setSelectedGroup(group);
                      setShowMembersModal(true);
                    }}
                    className="flex-1 bg-blue-500 hover:bg-blue-600 text-white text-sm py-2 px-3 rounded"
                  >
                    👥 Membri
                  </button>
                  <button
                    onClick={() => handleEditGroup(group)}
                    className="bg-yellow-500 hover:bg-yellow-600 text-white text-sm py-2 px-3 rounded"
                  >
                    ✏️ Modifica
                  </button>
                  <button
                    onClick={() => handleDeleteGroup(group.group_id)}
                    className="bg-red-500 hover:bg-red-600 text-white text-sm py-2 px-3 rounded"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal Creazione Gruppo */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                ➕ Crea Nuovo Gruppo
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nome gruppo *
                  </label>
                  <input
                    type="text"
                    value={newGroup.name}
                    onChange={(e) => setNewGroup({...newGroup, name: e.target.value})}
                    placeholder="es: Team Vendite"
                    className="w-full border border-gray-300 rounded px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Descrizione
                  </label>
                  <textarea
                    value={newGroup.description}
                    onChange={(e) => setNewGroup({...newGroup, description: e.target.value})}
                    placeholder="Descrizione del gruppo..."
                    rows={3}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Colore gruppo
                  </label>
                  <div className="flex space-x-2">
                    {predefinedColors.map(color => (
                      <button
                        key={color}
                        onClick={() => setNewGroup({...newGroup, color})}
                        className={`w-8 h-8 rounded-full border-2 ${
                          newGroup.color === color ? 'border-gray-800' : 'border-gray-300'
                        }`}
                        style={{ backgroundColor: color }}
                        title={color}
                      />
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewGroup({ name: '', description: '', color: '#3B82F6' });
                  }}
                  className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded"
                >
                  Annulla
                </button>
                <button
                  onClick={handleCreateGroup}
                  disabled={!newGroup.name.trim()}
                  className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded disabled:bg-gray-300"
                >
                  ➕ Crea Gruppo
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Modifica Gruppo */}
      {showEditModal && selectedGroup && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                ✏️ Modifica Gruppo: {selectedGroup.name}
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nome gruppo *
                  </label>
                  <input
                    type="text"
                    value={editGroup.name}
                    onChange={(e) => setEditGroup({...editGroup, name: e.target.value})}
                    placeholder="es: Team Vendite"
                    className="w-full border border-gray-300 rounded px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Descrizione
                  </label>
                  <textarea
                    value={editGroup.description}
                    onChange={(e) => setEditGroup({...editGroup, description: e.target.value})}
                    placeholder="Descrizione del gruppo..."
                    rows={3}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Colore gruppo
                  </label>
                  <div className="flex space-x-2">
                    {predefinedColors.map(color => (
                      <button
                        key={color}
                        onClick={() => setEditGroup({...editGroup, color})}
                        className={`w-8 h-8 rounded-full border-2 ${
                          editGroup.color === color ? 'border-gray-800' : 'border-gray-300'
                        }`}
                        style={{ backgroundColor: color }}
                        title={color}
                      />
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowEditModal(false);
                    setSelectedGroup(null);
                    setEditGroup({ name: '', description: '', color: '#3B82F6' });
                  }}
                  className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded"
                >
                  Annulla
                </button>
                <button
                  onClick={handleUpdateGroup}
                  disabled={!editGroup.name.trim()}
                  className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded disabled:bg-gray-300"
                >
                  ✏️ Aggiorna Gruppo
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Gestione Membri */}
      {showMembersModal && selectedGroup && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-11/12 md:w-3/4 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                👥 Gestione Membri: {selectedGroup.name}
              </h3>

              {/* Membri attuali */}
              <div className="mb-6">
                <h4 className="font-medium mb-2">Membri attuali ({selectedGroup.members_count})</h4>
                {selectedGroup.members && selectedGroup.members.length > 0 ? (
                  <div className="max-h-40 overflow-y-auto border border-gray-200 rounded">
                    {selectedGroup.members.map((member, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 border-b last:border-b-0">
                        <div>
                          <span className="font-medium">{member.user_id}</span>
                          <span className="text-sm text-gray-500 ml-2">({member.role_in_group})</span>
                        </div>
                        <button
                          onClick={() => handleRemoveMember(selectedGroup.group_id, member.user_id)}
                          className="text-red-600 hover:text-red-800 text-sm"
                        >
                          ❌ Rimuovi
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">Nessun membro nel gruppo</p>
                )}
              </div>

              {/* Aggiungi membri */}
              <div className="mb-4">
                <h4 className="font-medium mb-2">Aggiungi membri</h4>
                <div className="max-h-32 overflow-y-auto border border-gray-300 rounded p-2">
                  {users.filter(user => 
                    !selectedGroup.members || !selectedGroup.members.some(member => member.user_id === user.id)
                  ).map(user => (
                    <label key={user.id} className="flex items-center py-1">
                      <input
                        type="checkbox"
                        checked={selectedUsers.includes(user.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedUsers([...selectedUsers, user.id]);
                          } else {
                            setSelectedUsers(selectedUsers.filter(id => id !== user.id));
                          }
                        }}
                        className="mr-2"
                      />
                      <span className="text-sm">
                        {user.email} ({user.role})
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowMembersModal(false);
                    setSelectedUsers([]);
                  }}
                  className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded"
                >
                  Chiudi
                </button>
                <button
                  onClick={handleAddMembersToGroup}
                  disabled={selectedUsers.length === 0}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded disabled:bg-gray-300"
                >
                  ➕ Aggiungi Selezionati ({selectedUsers.length})
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GroupManagement;
