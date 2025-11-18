import React, { useState } from 'react';

function ScanPathsEditor({ scanPaths, onSave, loading }) {
  const [paths, setPaths] = useState(scanPaths || []);
  const [newPath, setNewPath] = useState('');
  const [editMode, setEditMode] = useState(false);

  const handleAdd = () => {
    if (newPath && !paths.includes(newPath)) {
      setPaths([...paths, newPath]);
      setNewPath('');
    }
  };

  const handleRemove = (idx) => {
    setPaths(paths.filter((_, i) => i !== idx));
  };

  const handleSave = () => {
    onSave(paths);
    setEditMode(false);
  };

  return (
    <div>
      {!editMode ? (
        <div>
          <ul className="list-disc ml-4">
            {paths.length > 0 ? paths.map((p, i) => <li key={i}>{p}</li>) : <li className="text-gray-400">Nessun percorso configurato</li>}
          </ul>
          <button className="mt-2 px-2 py-1 text-xs bg-blue-500 text-white rounded" onClick={() => setEditMode(true)}>
            Modifica
          </button>
        </div>
      ) : (
        <div>
          <ul className="list-disc ml-4 mb-2">
            {paths.map((p, i) => (
              <li key={i} className="flex items-center">
                <span className="mr-2">{p}</span>
                <button className="text-xs text-red-500 ml-2" onClick={() => handleRemove(i)} disabled={loading}>Rimuovi</button>
              </li>
            ))}
          </ul>
          <div className="flex items-center mb-2">
            <input
              type="text"
              value={newPath}
              onChange={e => setNewPath(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1 text-xs mr-2"
              placeholder="Aggiungi percorso..."
              disabled={loading}
            />
            <button className="px-2 py-1 text-xs bg-green-500 text-white rounded" onClick={handleAdd} disabled={loading || !newPath}>
              Aggiungi
            </button>
          </div>
          <div className="flex space-x-2">
            <button className="px-2 py-1 text-xs bg-blue-500 text-white rounded" onClick={handleSave} disabled={loading}>
              Salva
            </button>
            <button className="px-2 py-1 text-xs bg-gray-300 rounded" onClick={() => setEditMode(false)} disabled={loading}>
              Annulla
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ScanPathsEditor;
