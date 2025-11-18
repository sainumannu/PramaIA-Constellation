// LoginPage.js
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { endpoints } from './services/api';
import { decodeJwtPayload } from './utils/authUtils'; // Importa la funzione helper
import config from './config';

function LoginPage({ onLoginSuccess }) { // Aggiunta la prop onLoginSuccess
  const navigate = useNavigate();
  const [localUsername, setLocalUsername] = useState('');
  const [localPassword, setLocalPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Usa la stessa chiave 'token' usata in useAuth
    const token = localStorage.getItem("token");
    if (token) {
      // Potresti voler verificare la validità del token qui prima di navigare
      // Ma per ora, se il token esiste, assumiamo che sia valido e navighiamo.
      // L'hook useAuth in App.js si occuperà di verificarlo e, se non valido,
      // l'utente verrà reindirizzato nuovamente al login.
      navigate("/app", { replace: true });
    }
  }, [navigate]);

  const handleMicrosoftLogin = () => {
    setLoading(true);
    window.location.href = `${config.BACKEND_URL}/auth/login`;
  };

  // Non è più necessaria handleTokenAndRole separata,
  // la logica è integrata in onLoginSuccess (che è auth.updateUser)

  const handleLocalLogin = async (e) => {
    console.log("LoginPage: handleLocalLogin avviato.");
    e.preventDefault();
    setError('');
    setLoading(true);

    if (!localUsername || !localPassword) {
      setError('Username e password sono obbligatori.');
      setLoading(false);
      console.log("LoginPage: Username o password mancanti.");
      return;
    }

    try {
      const formData = new URLSearchParams();
      formData.append('username', localUsername);
      formData.append('password', localPassword);

      console.log("LoginPage: Tentativo di chiamata a /auth/token/local...");
      const response = await endpoints.auth.localLogin(formData);

      if (response.data && response.data.access_token) {
        console.log("LoginPage: Login locale riuscito, token ricevuto:", response.data.access_token);
        console.log("Token decodificato:", decodeJwtPayload(response.data.access_token));
        onLoginSuccess(response.data.access_token);
        navigate("/app", { replace: true });
        console.log("Navigazione verso /app eseguita");
      } else {
        console.log("LoginPage: Risposta di login non valida o token mancante.");
        setError('Risposta di login non valida.');
      }
    } catch (err) {
      console.error("LoginPage: Errore nel blocco try/catch di handleLocalLogin:", err);
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Errore durante il login locale. Riprova.');
      }
    } finally {
      console.log("LoginPage: Blocco finally di handleLocalLogin eseguito. setLoading(false).");
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="p-8 bg-white shadow-xl rounded-lg w-full max-w-md">
        <h1 className="text-3xl font-bold text-center text-blue-700 mb-6">
          Prama AI - Login
        </h1>
        {error && <p className="mb-4 text-center text-red-500 bg-red-100 p-3 rounded">{error}</p>}

        <form onSubmit={handleLocalLogin} className="mb-6">
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={localUsername}
              onChange={(e) => setLocalUsername(e.target.value)}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              placeholder="Il tuo username"
              disabled={loading}
            />
          </div>
          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={localPassword}
              onChange={(e) => setLocalPassword(e.target.value)}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline"
              placeholder="******************"
              disabled={loading}
            />
          </div>
          <button type="submit" disabled={loading} className="w-full bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50">
            {loading ? 'Login in corso...' : 'Login con Credenziali'}
          </button>
        </form>

        <div className="my-4 text-center">
          <p className="text-sm text-gray-600">
            Non hai un account?{' '}
            <a href="/register" className="text-blue-700 hover:text-blue-800 font-semibold">
              Registrati
            </a>
          </p>
        </div>

        <div className="my-4 flex items-center before:mt-0.5 before:flex-1 before:border-t before:border-neutral-300 after:mt-0.5 after:flex-1 after:border-t after:border-neutral-300">
          <p className="mx-4 mb-0 text-center font-semibold text-slate-500">O</p>
        </div>

        <button onClick={handleMicrosoftLogin} disabled={loading} className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-150 ease-in-out disabled:opacity-50">
          {loading ? 'Attendere...' : 'Login con Microsoft'}
        </button>
        <p className="text-center text-xs text-gray-600 mt-8">
          Sarai reindirizzato alla pagina di login di Microsoft.
        </p>
      </div>
    </div>
  );
}

export default LoginPage;
