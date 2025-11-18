import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { USERS_BASE_URL } from '../config/appConfig';

function UserManager() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  // TODO: Aggiungere stati per la gestione dei form (creazione/modifica utente) e modali

  const fetchUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.get(`${USERS_BASE_URL}/`);
      setUsers(response.data || []);
    } catch (err) {
      console.error('Errore nel recupero utenti:', err);
      setError(err.response?.data?.detail || 'Impossibile caricare la lista utenti. Assicurati di avere i permessi di amministratore.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // TODO: Implementare funzioni per handleCreateUser, handleUpdateUser, handleDeleteUser

  if (loading) {
    return <div className="p-6 text-center">Caricamento utenti...</div>;
  }

  if (error) {
    return <div className="p-6 text-center text-red-500 bg-red-100 border border-red-400 rounded-md">{error}</div>;
  }

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Gestione Utenti</h2>

      {/* TODO: Aggiungere pulsante e modale/form per creare un nuovo utente */}
      <div className="mb-6">
        <button
          className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded"
          onClick={() => alert('TODO: Apri modale creazione utente')} // Placeholder
        >
          Aggiungi Nuovo Utente
        </button>
      </div>

      {users.length === 0 && !loading && !error && (
        <p className="text-gray-600">Nessun utente trovato.</p>
      )}

      {users.length > 0 && (
        <div className="overflow-x-auto bg-white shadow-md rounded-lg">
          <table className="min-w-full table-auto">
            <thead className="bg-gray-200">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Username</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ruolo</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Attivo</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">{user.id}</td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">{user.username}</td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">{user.name || 'N/D'}</td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">{user.email || 'N/D'}</td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">{user.role}</td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                      {user.is_active ? 'Sì' : 'No'}
                    </span>
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm font-medium">
                    <button 
                      onClick={() => alert(`TODO: Modifica utente ${user.id}`)} 
                      className="text-indigo-600 hover:text-indigo-900 mr-3"
                    >
                      Modifica
                    </button>
                    <button 
                      onClick={() => alert(`TODO: ${user.is_active ? 'Disabilita' : 'Abilita'} utente ${user.id}`)} 
                      className={`mr-3 ${user.is_active ? 'text-yellow-600 hover:text-yellow-900' : 'text-green-600 hover:text-green-900'}`}
                    >
                      {user.is_active ? 'Disabilita' : 'Abilita'}
                    </button>
                    <button onClick={() => alert(`TODO: Elimina utente ${user.id}`)} className="text-red-600 hover:text-red-900">
                      Elimina
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default UserManager;
