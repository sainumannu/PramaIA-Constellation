import React, { useState, useEffect } from 'react';
import axios from 'axios';
import config from '../config';

function LLMProviderSelect({ value, onChange }) {
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${config.BACKEND_URL}/llm/providers`)
      .then(res => setProviders(res.data))
      .catch(() => setProviders(['openai']))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <label className="mr-2 font-semibold">Provider:</label>
      {loading ? (
        <span>Caricamento provider...</span>
      ) : (
        <select value={value} onChange={e => onChange(e.target.value)} className="p-2 border rounded">
          {providers.map(p => (
            <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
          ))}
        </select>
      )}
    </div>
  );
}

export default LLMProviderSelect;
