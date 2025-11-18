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
  
  // State per tab attivo
  const [activeTab, setActiveTab] = useState('users'); // 'users' o 'groups'

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Carica dati dal localStorage
      const savedUsers = localStorage.getItem('pramaia_users');
      const savedDomains = localStorage.getItem('pramaia_domains');
      
      // Usa dati salvati o dati di default
      const defaultUsers = [
        { id: '1', username: 'Admin', email: 'admin@pramaia.com', role: 'admin', is_active: true },
        { id: '2', username: 'Mario Rossi', email: 'user1@example.com', role: 'user', is_active: true },
        { id: '3', username: 'Giulia Verde', email: 'user2@example.com', role: 'user', is_active: false }
      ];
      
      const defaultDomains = ['example.com', 'pramaia.com'];
      
      setUsers(savedUsers ? JSON.parse(savedUsers) : defaultUsers);
      setDomains(savedDomains ? JSON.parse(savedDomains) : defaultDomains);
      
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
    
    const updatedUsers = users.filter(user => user.id !== userId);
    setUsers(updatedUsers);
    localStorage.setItem('pramaia_users', JSON.stringify(updatedUsers));
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
        setMessage('Utente aggiornato con successo');
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
        setMessage('Utente creato con successo');
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
    return user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
           (user.username && user.username.toLowerCase().includes(searchTerm.toLowerCase())) ||
           user.role.toLowerCase().includes(searchTerm.toLowerCase());
  });

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
          <h1 className="text-2xl font-bold text-blue-700">👥 Gestione Utenti e Gruppi</h1>
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

        {/* Tab Navigation */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              <button
                onClick={() => setActiveTab('users')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'users'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                👤 Gestione Utenti
              </button>
              <button
                onClick={() => setActiveTab('groups')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'groups'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                👥 Gestione Gruppi
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'users' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Sezione Utenti */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-semibold text-gray-900">Utenti Registrati</h2>
                    <button
                      onClick={handleCreateUser}
                      className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg"
                    >
                      ➕ Nuovo Utente
                    </button>
                  </div>
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

            {/* Sezione Domini */}
            <div className="space-y-6">
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
            </div>
          </div>
        )}

        {activeTab === 'groups' && (
          <div>
            <GroupManagement />
          </div>
        )}

        {/* Modal per utente */}
        {showModal && (
          <UserFormModal
            isOpen={showModal}
            user={selectedUser}
            groups={[]} // Passa array vuoto per ora, i gruppi saranno gestiti separatamente
            onSave={handleSaveUser}
            onClose={() => setShowModal(false)}
          />
        )}
      </div>
    </div>
  );
}

export default UserManagementPage;
