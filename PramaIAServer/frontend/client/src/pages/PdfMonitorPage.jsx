import React from 'react';
import { Outlet } from 'react-router-dom'; // Aggiunto Outlet
import SidebarNavItem from '../components/SidebarNavItem'; // Importa il nuovo componente
// import { useAuth } from '../contexts/AuthContext'; // Esempio se avessi un AuthContext

function LayoutWithSidebar({ children, currentUserRole, onLogout, onNavigate }) { // Aggiunte props

  // const { currentUser, logout } = useAuth(); // Esempio da AuthContext
  // currentUserRole ora viene passato come prop da AppContent

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-md p-4 hidden md:flex flex-col">
        <h2 className="text-xl font-bold text-blue-700 mb-6">📁 Prama AI</h2>

        <nav className="flex-1 space-y-1"> {/* Cambiato div in nav per semantica */}
          <SidebarNavItem to="/app/chat" label="Chat" icon="💬" onClick={() => onNavigate('chat')} />
          <SidebarNavItem to="/app/documenti" label="Documenti" icon="📂" onClick={() => onNavigate('documenti')} />
          <SidebarNavItem to="/app/history" label="Cronologia" icon="🕓" onClick={() => onNavigate('history')} />
          <SidebarNavItem to="/app/notebooks" label="Notebooks" icon="📒" onClick={() => onNavigate('notebooks')} />
          {currentUserRole === 'admin' && <SidebarNavItem to="/app/dashboard" label="Dashboard" icon="🛠️" onClick={() => onNavigate('dashboard')} />}
          {currentUserRole === 'admin' && <SidebarNavItem to="/app/admin/users" label="Gestione Utenti" icon="👥" onClick={() => onNavigate('admin/users')} />}
        </nav>


        <div className="mt-auto pt-4 border-t border-gray-200"> {/* Bordo più leggero */}
          <p className="text-sm text-gray-600 mb-2">
            Ruolo: <strong className="font-semibold text-gray-800">{currentUserRole || 'Non definito'}</strong>
          </p>
          <button
            className="w-full text-left px-4 py-2 rounded bg-red-600 text-white hover:bg-red-700 flex items-center gap-2" // Stile bottone
            onClick={onLogout} // Usa la funzione onLogout passata da AppContent
          >
            <span className="text-lg">🔒</span>
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto p-6">{children || <Outlet />}</main> {/* Aggiunto padding e Outlet come fallback */}
    </div>
  );
}

export default LayoutWithSidebar;