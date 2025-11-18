import React, { useState, useEffect } from 'react';

function UserFormModal({ isOpen, onClose, onSave, user, groups = [] }) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'user',
    groups: []
  });
  const [error, setError] = useState('');

  const isEditing = user && user.id;

  useEffect(() => {
    if (isEditing) {
      setFormData({
        username: user.username || '',
        email: user.email,
        password: '',
        role: user.role,
        groups: user.groups || []
      });
    } else {
      setFormData({ 
        username: '', 
        email: '', 
        password: '', 
        role: 'user',
        groups: []
      });
    }
    setError('');
  }, [user, isOpen, isEditing]);

  if (!isOpen) {
    return null;
  }

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleGroupToggle = (groupId) => {
    const currentGroups = formData.groups || [];
    const newGroups = currentGroups.includes(groupId)
      ? currentGroups.filter(id => id !== groupId)
      : [...currentGroups, groupId];
    
    setFormData(prev => ({ ...prev, groups: newGroups }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.username) {
      setError('L\'username è obbligatorio.');
      return;
    }
    if (!formData.email) {
      setError('L\'email è obbligatoria.');
      return;
    }
    if (!isEditing && !formData.password) {
      setError('La password è obbligatoria per i nuovi utenti.');
      return;
    }
    onSave(formData, user?.id);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-md">
        <h2 className="text-2xl font-bold mb-4 text-blue-700">{isEditing ? 'Modifica Utente' : 'Aggiungi Nuovo Utente'}</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="username">Username</label>
            <input
              type="text"
              name="username"
              id="username"
              value={formData.username}
              onChange={handleChange}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            />
          </div>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="email">Email</label>
            <input
              type="email"
              name="email"
              id="email"
              value={formData.email}
              onChange={handleChange}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            />
          </div>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="password">Password</label>
            <input
              type="password"
              name="password"
              id="password"
              value={formData.password}
              onChange={handleChange}
              placeholder={isEditing ? 'Lascia vuoto per non modificare' : ''}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            />
          </div>
          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="role">Ruolo</label>
            <select name="role" id="role" value={formData.role} onChange={handleChange} className="shadow border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          {/* Sezione Gruppi */}
          {groups.length > 0 && (
            <div className="mb-6">
              <label className="block text-gray-700 text-sm font-bold mb-2">Gruppi</label>
              <div className="max-h-32 overflow-y-auto border border-gray-300 rounded p-2 bg-gray-50">
                {groups.map((group) => (
                  <label key={group.group_id} className="flex items-center py-1 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.groups.includes(group.group_id)}
                      onChange={() => handleGroupToggle(group.group_id)}
                      className="mr-2"
                    />
                    <div className="flex items-center">
                      <div 
                        className="w-4 h-4 rounded-full mr-2"
                        style={{ backgroundColor: group.color }}
                      ></div>
                      <span className="text-sm">{group.name}</span>
                      {group.description && (
                        <span className="text-xs text-gray-500 ml-1">
                          ({group.description})
                        </span>
                      )}
                    </div>
                  </label>
                ))}
              </div>
              {formData.groups.length > 0 && (
                <div className="mt-1 text-xs text-gray-600">
                  Gruppi selezionati: {formData.groups.map(gId => {
                    const group = groups.find(g => g.group_id === gId);
                    return group ? group.name : gId;
                  }).join(', ')}
                </div>
              )}
            </div>
          )}

          {error && <p className="text-red-500 text-xs italic mb-4">{error}</p>}
          <div className="flex items-center justify-end gap-2">
            <button type="button" onClick={onClose} className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">Annulla</button>
            <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">Salva</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default UserFormModal;
