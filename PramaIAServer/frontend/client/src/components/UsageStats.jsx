import React, { useEffect, useState } from "react";
import axios from "axios";
import config from '../config';

function UsageStats() {
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [ranking, setRanking] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchRanking = async () => {
    setLoading(true);
    try {
      const params = {};
      if (fromDate) params.from_date = fromDate;
      if (toDate) params.to_date = toDate;
      const res = await axios.get(`${config.BACKEND_URL}/usage_ranking`, { params });
      setRanking(res.data);
    } catch (err) {
      setRanking([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRanking();
    // eslint-disable-next-line
  }, []);

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-bold mb-6 text-blue-700">📊 Utilizzo Token per Utente</h2>
      <div className="mb-6 flex gap-4 items-end">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Dal:</label>
          <input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)} className="form-input p-2 border rounded-md shadow-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Al:</label>
          <input type="date" value={toDate} onChange={e => setToDate(e.target.value)} className="form-input p-2 border rounded-md shadow-sm" />
        </div>
        <button className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-md shadow-sm" onClick={fetchRanking}>Filtra</button>
      </div>
      {loading ? (
        <p>Caricamento...</p>
      ) : (
        <ol className="bg-white rounded-lg shadow p-6">
          {ranking.length === 0 && <li>Nessun dato disponibile per il periodo selezionato.</li>}
          {ranking.map((u, idx) => (
            <li key={u.user_id} className="mb-2">
              <span className="font-bold">{idx + 1}.</span> <span className="font-mono">{u.user_id}</span> — <span className="text-blue-700 font-semibold">{u.tokens_used}</span> token
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

export default UsageStats;
