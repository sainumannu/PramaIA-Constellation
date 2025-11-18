import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

function SidebarNavItem({ to, label, icon }) { // Aggiunto 'icon' opzionale
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = location.pathname === to;

  const activeClasses = isActive ? 'bg-blue-100 text-blue-700 font-semibold' : 'hover:bg-gray-200';

  return (
    <button
      className={`w-full text-left px-4 py-2 rounded flex items-center gap-2 ${activeClasses}`}
      onClick={() => navigate(to)}
      aria-current={isActive ? 'page' : undefined}
    >
      {icon && <span className="text-lg">{icon}</span>} {/* Mostra l'icona se fornita */}
      <span>{label}</span>
    </button>
  );
}

export default SidebarNavItem;
