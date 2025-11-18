import React, { useState, useEffect } from 'react';
import UserFormModal from '../components/UserFormModal';
import GroupManagement from '../components/GroupManagement';

function UserManagementPage() {
  // State per gestione utenti
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  // State per gestione domini
  const [domains, setDomains] = useState([]);
  const [newDomain, setNewDomain] = useState('');
  
  // Nuovi stati per funzionalità avanzate
  const [filterRole, setFilterRole] = useState('all');
  const [filterGroup, setFilterGroup] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [showImportModal, setShowImportModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showStatsModal, setShowStatsModal] = useState(false);
  const [auditLog, setAuditLog] = useState([]);
  const [showAuditModal, setShowAuditModal] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Carica dati dal localStorage
      const savedUsers = localStorage.getItem('pramaia_users');
      const savedDomains = localStorage.getItem('pramaia_domains');
      const savedAuditLog = localStorage.getItem('pramaia_audit_log');
      
      // Usa dati salvati o dati di default
      const defaultUsers = [
        { id: '1', username: 'Admin', email: 'admin@pramaia.com', role: 'admin', is_active: true, groups: ['1'] },
        { id: '2', username: 'Mario Rossi', email: 'user1@example.com', role: 'user', is_active: true, groups: ['1', '2'] },
        { id: '3', username: 'Giulia Verde', email: 'user2@example.com', role: 'user', is_active: false, groups: ['3'] }
      ];
      
      const defaultDomains = ['example.com', 'pramaia.com'];
      
      setUsers(savedUsers ? JSON.parse(savedUsers) : defaultUsers);
      setDomains(savedDomains ? JSON.parse(savedDomains) : defaultDomains);
      setAuditLog(savedAuditLog ? JSON.parse(savedAuditLog) : []);
      
      // Salva i dati di default se non esistono
      if (!savedUsers) localStorage.setItem('pramaia_users', JSON.stringify(defaultUsers));
      if (!savedDomains) localStorage.setItem('pramaia_domains', JSON.stringify(defaultDomains));
      
      setLoading(false);
      
    } catch (error) {
      console.error('Errore caricamento dati:', error);
      setMessage('Errore nel caricamento dei dati: ' + error.message);
      setLoading(false);
    }
  };

  const handleCreateUser = () => {
    setSelectedUser(null);
    setShowModal(true);
  };

  const handleEditUser = (user) => {
    setSelectedUser(user);
    setShowModal(true);
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Sei sicuro di voler eliminare questo utente?')) {
      return;
    }
    
    // Trova l'utente da eliminare per sapere a quali gruppi appartiene
    const userToDelete = users.find(user => user.id === userId);
    
    // Rimuovi l'utente dalla lista
    const updatedUsers = users.filter(user => user.id !== userId);
    setUsers(updatedUsers);
    localStorage.setItem('pramaia_users', JSON.stringify(updatedUsers));
    
    // Aggiorna il contatore dei membri nei gruppi
    if (userToDelete && userToDelete.groups) {
      const updatedGroups = groups.map(group => {
        if (userToDelete.groups.includes(group.group_id)) {
          return {
            ...group,
            members_count: Math.max(0, group.members_count - 1)
          };
        }
        return group;
      });
      setGroups(updatedGroups);
      localStorage.setItem('pramaia_groups', JSON.stringify(updatedGroups));
    }
    
    setMessage('Utente eliminato con successo');
  };

  const handleSaveUser = async (userData, userId) => {
    try {
      if (selectedUser && userId) {
        // Aggiorna utente esistente
        const updatedUsers = users.map(user => 
          user.id === userId 
            ? { ...user, ...userData, id: userId }
            : user
        );
        setUsers(updatedUsers);
        localStorage.setItem('pramaia_users', JSON.stringify(updatedUsers));
        
        // Aggiorna il contatore dei membri nei gruppi (per modifica utente)
        if (userData.groups) {
          const updatedGroups = groups.map(group => {
            const wasInGroup = selectedUser.groups?.includes(group.group_id);
            const isNowInGroup = userData.groups.includes(group.group_id);
            
            if (!wasInGroup && isNowInGroup) {
              // Aggiunto al gruppo
              return { ...group, members_count: group.members_count + 1 };
            } else if (wasInGroup && !isNowInGroup) {
              // Rimosso dal gruppo  
              return { ...group, members_count: Math.max(0, group.members_count - 1) };
            }
            return group;
          });
          setGroups(updatedGroups);
          localStorage.setItem('pramaia_groups', JSON.stringify(updatedGroups));
          
          // Messaggio con nomi corretti dei gruppi - usa l'array originale
          if (userData.groups.length > 0) {
            const groupNames = userData.groups.map(gId => {
              const group = groups.find(g => g.group_id === gId);
              return group ? group.name : `Gruppo ${gId}`;
            }).join(', ');
            setMessage(`Utente aggiornato con successo e assegnato ai gruppi: ${groupNames}`);
          } else {
            setMessage('Utente aggiornato con successo');
          }
        } else {
          setMessage('Utente aggiornato con successo');
        }
        
        // Audit log per modifica utente
        addAuditEntry('Update', 'User', `Updated user: ${userData.username || userData.email}`);
      } else {
        // Crea nuovo utente
        const newUser = {
          ...userData,
          id: Date.now().toString(),
          is_active: true
        };
        const updatedUsers = [...users, newUser];
        setUsers(updatedUsers);
        localStorage.setItem('pramaia_users', JSON.stringify(updatedUsers));
        
        // Aggiorna il contatore dei membri nei gruppi selezionati
        if (userData.groups && userData.groups.length > 0) {
          const updatedGroups = groups.map(group => {
            if (userData.groups.includes(group.group_id)) {
              return {
                ...group,
                members_count: group.members_count + 1
              };
            }
            return group;
          });
          setGroups(updatedGroups);
          localStorage.setItem('pramaia_groups', JSON.stringify(updatedGroups));
          
          // Messaggio con nomi corretti dei gruppi - usa l'array originale prima dell'aggiornamento
          const groupNames = userData.groups.map(gId => {
            const group = groups.find(g => g.group_id === gId);
            return group ? group.name : `Gruppo ${gId}`;
          }).join(', ');
          
          setMessage(`Utente creato con successo e assegnato ai gruppi: ${groupNames}`);
        } else {
          setMessage('Utente creato con successo');
        }
      }
      setShowModal(false);
    } catch (error) {
      setMessage('Errore nel salvataggio dell\'utente: ' + error.message);
    }
  };

  const handleAddDomain = async () => {
    if (!newDomain.trim()) return;
    const updatedDomains = [...domains, newDomain.trim()];
    setDomains(updatedDomains);
    localStorage.setItem('pramaia_domains', JSON.stringify(updatedDomains));
    setNewDomain('');
    setMessage('Dominio aggiunto con successo');
  };

  const handleRemoveDomain = async (domain) => {
    if (!window.confirm(`Rimuovere il dominio "${domain}"?`)) return;
    const updatedDomains = domains.filter(d => d !== domain);
    setDomains(updatedDomains);
    localStorage.setItem('pramaia_domains', JSON.stringify(updatedDomains));
    setMessage('Dominio rimosso con successo');
  };

  const filteredUsers = users.filter(user => {
    // Filtro per ricerca di testo
    const searchMatch = user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                       (user.username && user.username.toLowerCase().includes(searchTerm.toLowerCase())) ||
                       user.role.toLowerCase().includes(searchTerm.toLowerCase());
    
    // Filtro per ruolo
    const roleMatch = filterRole === 'all' || user.role === filterRole;
    
    // Filtro per stato
    const statusMatch = filterStatus === 'all' || 
                       (filterStatus === 'active' && user.is_active) ||
                       (filterStatus === 'inactive' && !user.is_active);
    
    // Filtro per gruppo
    const groupMatch = filterGroup === 'all' || 
                      (user.groups && user.groups.includes(filterGroup));
    
    return searchMatch && roleMatch && statusMatch && groupMatch;
  });

  const predefinedColors = [
    '#3B82F6', '#EF4444', '#10B981', '#F59E0B', 
    '#8B5CF6', '#F97316', '#06B6D4', '#84CC16'
  ];

  // Funzione per aggiungere un entry nell'audit log
  const addAuditEntry = (action, target, details = '') => {
    const entry = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      action,
      target,
      details,
      user: 'Admin' // In un'app reale, questo verrebbe dall'utente autenticato
    };
    
    const newLog = [entry, ...auditLog].slice(0, 100); // Mantieni solo gli ultimi 100 entry
    setAuditLog(newLog);
    localStorage.setItem('pramaia_audit_log', JSON.stringify(newLog));
  };

  // Funzione per calcolare statistiche
  const getStats = () => {
    const totalUsers = users.length;
    const activeUsers = users.filter(u => u.is_active).length;
    const inactiveUsers = totalUsers - activeUsers;
    const adminUsers = users.filter(u => u.role === 'admin').length;
    const regularUsers = users.filter(u => u.role === 'user').length;
    
    const groupStats = groups.map(group => ({
      name: group.name,
      count: group.members_count,
      color: group.color
    }));

    return {
      totalUsers,
      activeUsers,
      inactiveUsers,
      adminUsers,
      regularUsers,
      totalGroups: groups.length,
      totalDomains: domains.length,
      groupStats
    };
  };

  // Funzione per validare email con dominio autorizzato
  const isEmailDomainValid = (email) => {
    if (!email || !email.includes('@')) return false;
    const domain = email.split('@')[1];
    return domains.includes(domain);
  };

  // Funzione per generare password casuale
  const generateRandomPassword = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
    let password = '';
    for (let i = 0; i < 12; i++) {
      password += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return password;
  };

  // Funzione per esportare utenti in CSV
  const exportUsersToCSV = () => {
    const headers = ['Username', 'Email', 'Role', 'Status', 'Groups'];
    const csvData = users.map(user => [
      user.username || '',
      user.email,
      user.role,
      user.is_active ? 'Active' : 'Inactive',
      user.groups?.map(gId => {
        const group = groups.find(g => g.group_id === gId);
        return group ? group.name : gId;
      }).join(';') || ''
    ]);

    const csvContent = [headers, ...csvData]
      .map(row => row.map(field => `"${field}"`).join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `pramaia_users_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    addAuditEntry('Export', 'Users', `Exported ${users.length} users to CSV`);
    setMessage('Utenti esportati con successo in CSV');
  };

  // Funzione per importare utenti da CSV
  const handleImportCSV = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const csv = e.target.result;
        const lines = csv.split('\n');
        const headers = lines[0].split(',').map(h => h.replace(/"/g, '').trim());
        
        const importedUsers = [];
        let errors = [];
        
        for (let i = 1; i < lines.length; i++) {
          if (!lines[i].trim()) continue;
          
          const values = lines[i].split(',').map(v => v.replace(/"/g, '').trim());
          const userData = {};
          
          headers.forEach((header, index) => {
            userData[header.toLowerCase()] = values[index] || '';
          });
          
          // Validazione base
          if (!userData.email || !userData.email.includes('@')) {
            errors.push(`Riga ${i + 1}: Email non valida`);
            continue;
          }
          
          if (!isEmailDomainValid(userData.email)) {
            errors.push(`Riga ${i + 1}: Dominio email non autorizzato`);
            continue;
          }
          
          // Controlla duplicati
          if (users.find(u => u.email === userData.email)) {
            errors.push(`Riga ${i + 1}: Email già esistente`);
            continue;
          }
          
          const newUser = {
            id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
            username: userData.username || userData.email.split('@')[0],
            email: userData.email,
            role: userData.role === 'admin' ? 'admin' : 'user',
            is_active: userData.status !== 'Inactive',
            groups: userData.groups ? userData.groups.split(';').map(groupName => {
              const group = groups.find(g => g.name.trim() === groupName.trim());
              return group ? group.group_id : null;
            }).filter(Boolean) : []
          };
          
          importedUsers.push(newUser);
        }
        
        if (importedUsers.length > 0) {
          const updatedUsers = [...users, ...importedUsers];
          setUsers(updatedUsers);
          localStorage.setItem('pramaia_users', JSON.stringify(updatedUsers));
          
          addAuditEntry('Import', 'Users', `Imported ${importedUsers.length} users from CSV`);
          setMessage(`Importati ${importedUsers.length} utenti con successo${errors.length > 0 ? `. Errori: ${errors.length}` : ''}`);
        }
        
        if (errors.length > 0) {
          console.warn('Errori importazione:', errors);
        }
        
      } catch (error) {
        setMessage('Errore nell\'importazione del file CSV: ' + error.message);
      }
    };
    
    reader.readAsText(file);
    event.target.value = ''; // Reset input
  };

  if (loading) {
    return (
      <div className="p-6 bg-gray-50 min-h-screen">
        <div className="max-w-6xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded mb-6 w-1/3"></div>
            <div className="space-y-4">
              <div className="h-6 bg-gray-200 rounded"></div>
              <div className="h-6 bg-gray-200 rounded"></div>
              <div className="h-6 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-blue-700">👥 Gestione Utenti</h1>
          <div className="flex space-x-2">
            <button
              onClick={() => {
                if (window.confirm('Vuoi resettare tutti i dati ai valori di default?')) {
                  localStorage.removeItem('pramaia_users');
                  localStorage.removeItem('pramaia_domains');
                  localStorage.removeItem('pramaia_groups');
                  loadData();
                  setMessage('Dati resettati ai valori di default');
                }
              }}
              className="bg-gray-500 hover:bg-gray-600 text-white px-3 py-2 rounded-lg text-sm"
            >
              🔄 Reset Dati
            </button>
            <button
              onClick={handleCreateUser}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg"
            >
              ➕ Nuovo Utente
            </button>
          </div>
        </div>

        {message && (
          <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-6">
            {message}
            <button 
              onClick={() => setMessage('')}
              className="float-right text-blue-700 hover:text-blue-900"
            >
              ✕
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Sezione Utenti */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Utenti Registrati</h2>
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Cerca utenti..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Utente
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Ruolo
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Gruppi
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Stato
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Azioni
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredUsers.map((user) => (
                      <tr key={user.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <div>
                            <div className="font-medium text-gray-900">
                              {user.username || user.email}
                            </div>
                            {user.username && (
                              <div className="text-sm text-gray-500">{user.email}</div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            user.role === 'admin' 
                              ? 'bg-red-100 text-red-800' 
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {user.role}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <div className="flex flex-wrap gap-1">
                            {user.groups?.map(groupId => {
                              const group = groups.find(g => g.group_id === groupId);
                              return group ? (
                                <span 
                                  key={groupId} 
                                  className="px-2 py-1 rounded-full text-xs text-white"
                                  style={{ backgroundColor: group.color }}
                                >
                                  {group.name}
                                </span>
                              ) : null;
                            }) || <span className="text-gray-400 text-xs">Nessun gruppo</span>}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            user.is_active 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {user.is_active ? 'Attivo' : 'Inattivo'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleEditUser(user)}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              ✏️ Modifica
                            </button>
                            <button
                              onClick={() => handleDeleteUser(user.id)}
                              className="text-red-600 hover:text-red-900"
                            >
                              🗑️ Elimina
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Sezione Domini e Gruppi */}
          <div className="space-y-6">
            {/* Domini */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Domini Autorizzati</h3>
              
              <div className="flex space-x-2 mb-4">
                <input
                  type="text"
                  value={newDomain}
                  onChange={(e) => setNewDomain(e.target.value)}
                  placeholder="nuovo-dominio.com"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded"
                />
                <button
                  onClick={handleAddDomain}
                  className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
                >
                  ➕
                </button>
              </div>
              
              <div className="space-y-2">
                {domains.map((domain, index) => (
                  <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <span className="text-sm">{domain}</span>
                    <button
                      onClick={() => handleRemoveDomain(domain)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      ❌
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Gestione Gruppi avanzata */}
            <GroupManagement />
          </div>
        </div>

        {/* Modal per utente */}
        {showModal && (
          <UserFormModal
            isOpen={showModal}
            user={selectedUser}
            groups={groups}
            onSave={handleSaveUser}
            onClose={() => setShowModal(false)}
          />
        )}

        {/* Modal per nuovo gruppo */}
        {showGroupModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Nuovo Gruppo</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nome</label>
                  <input
                    type="text"
                    value={newGroup.name}
                    onChange={(e) => setNewGroup({...newGroup, name: e.target.value})}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
                  <textarea
                    value={newGroup.description}
                    onChange={(e) => setNewGroup({...newGroup, description: e.target.value})}
                    className="w-full border border-gray-300 rounded px-3 py-2"
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Colore</label>
                  <div className="flex space-x-2">
                    {predefinedColors.map(color => (
                      <button
                        key={color}
                        onClick={() => setNewGroup({...newGroup, color})}
                        className={`w-8 h-8 rounded-full border-2 ${
                          newGroup.color === color ? 'border-gray-800' : 'border-gray-300'
                        }`}
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowGroupModal(false)}
                  className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded"
                >
                  Annulla
                </button>
                <button
                  onClick={handleCreateGroup}
                  className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
                >
                  Crea Gruppo
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default UserManagementPage;
