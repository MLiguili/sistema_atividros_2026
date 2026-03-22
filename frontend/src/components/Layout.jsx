import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Box, Users, ShoppingCart, LogOut, Calculator, Menu, X } from 'lucide-react';
import { useAutenticacao } from '../context/ContextoAutenticacao';

const Layout = ({ children }) => {
  const { usuario, logout } = useAutenticacao();
  const navegar = useNavigate();
  const [menuAberto, setMenuAberto] = useState(false);

  const handleLogout = () => {
    logout();
    navegar('/login');
  };

  const toggleMenu = () => setMenuAberto(!menuAberto);

  return (
    <div className="layout-root">
      {/* Mobile Header */}
      <header className="mobile-header">
        <button className="menu-toggle" onClick={toggleMenu}>
          {menuAberto ? <X size={24} /> : <Menu size={24} />}
        </button>
        <span className="mobile-logo">ATIVIDROS</span>
        <div style={{ width: 40 }} />
      </header>

      {/* Overlay para mobile */}
      {menuAberto && <div className="menu-overlay" onClick={() => setMenuAberto(false)} />}

      {/* Sidebar - Desktop e Mobile */}
      <aside className={`sidebar ${menuAberto ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2 className="sidebar-logo">ATIVIDROS</h2>
          <span className="sidebar-subtitle">SISTEMA DE GESTÃO v1</span>
        </div>

        <nav className="sidebar-nav">
          <MenuItem to="/" icone={<LayoutDashboard size={20} />} texto="Dashboard" onClick={() => setMenuAberto(false)} />
          <MenuItem to="/estoque" icone={<Box size={20} />} texto="Estoque" onClick={() => setMenuAberto(false)} />
          <MenuItem to="/clientes" icone={<Users size={20} />} texto="Clientes" onClick={() => setMenuAberto(false)} />
          <MenuItem to="/pedidos" icone={<ShoppingCart size={20} />} texto="Pedidos" onClick={() => setMenuAberto(false)} />
          <MenuItem to="/calculadora" icone={<Calculator size={20} />} texto="Calculadora" onClick={() => setMenuAberto(false)} />
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">
              {usuario?.nome_usuario?.[0]?.toUpperCase()}
            </div>
            <div className="user-details">
              <p className="user-name">{usuario?.nome_completo || usuario?.nome_usuario}</p>
              <p className="user-role">Administrador</p>
            </div>
          </div>
          <button className="btn btn-glass logout-btn" onClick={handleLogout}>
            <LogOut size={18} /> <span className="hide-mobile">Sair</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <div className="container fade-in">
          {children}
        </div>
      </main>

      <style>{`
        .layout-root {
          display: flex;
          min-height: 100vh;
          background-color: var(--bg-primary);
        }

        /* Mobile Header */
        .mobile-header {
          display: none;
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          height: 60px;
          background: var(--bg-secondary);
          border-bottom: 1px solid var(--glass-border);
          align-items: center;
          justify-content: space-between;
          padding: 0 1rem;
          z-index: 100;
        }

        .menu-toggle {
          background: none;
          border: none;
          color: var(--text-primary);
          cursor: pointer;
          padding: 0.5rem;
        }

        .mobile-logo {
          color: var(--accent-primary);
          font-weight: 700;
          font-size: 1.25rem;
          letter-spacing: 1px;
        }

        /* Sidebar */
        .sidebar {
          width: var(--sidebar-width);
          background-color: var(--bg-secondary);
          border-right: 1px solid var(--glass-border);
          display: flex;
          flex-direction: column;
          padding: 2rem 1.25rem;
          position: fixed;
          height: 100vh;
          z-index: 200;
          transition: transform 0.3s ease;
        }
        
        .sidebar:hover {
          box-shadow: 4px 0 24px rgba(0,0,0,0.2);
        }
        
        .sidebar-logo {
          font-size: 1.75rem;
          font-weight: 700;
          letter-spacing: 2px;
          margin-bottom: 0.5rem;
          background: linear-gradient(135deg, var(--accent-primary) 0%, #34d399 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .sidebar-header {
          margin-bottom: 2rem;
          padding: 0 0.5rem;
        }

        .sidebar-logo {
          color: var(--accent-primary);
          font-size: 1.5rem;
          letter-spacing: 1px;
          margin-bottom: 0.25rem;
        }

        .sidebar-subtitle {
          font-size: 0.75rem;
          color: var(--text-secondary);
        }

        .sidebar-nav {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .sidebar-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem 1rem;
          border-radius: 8px;
          color: var(--text-secondary);
          text-decoration: none;
          transition: all 0.2s ease;
        }

        .sidebar-item:hover {
          background-color: rgba(255, 255, 255, 0.05);
          color: var(--text-primary);
        }

        .sidebar-item.active {
          background-color: rgba(16, 185, 129, 0.15);
          color: var(--accent-primary);
          font-weight: 500;
        }

        .sidebar-footer {
          border-top: 1px solid var(--glass-border);
          padding-top: 1rem;
        }

        .user-info {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 1rem;
          padding: 0 0.5rem;
        }

        .user-avatar {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background-color: var(--accent-primary);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          font-size: 0.9rem;
        }

        .user-details {
          flex: 1;
        }

        .user-name {
          font-size: 0.9rem;
          font-weight: 500;
        }

        .user-role {
          font-size: 0.75rem;
          color: var(--text-secondary);
        }

        .logout-btn {
          width: 100%;
          justify-content: flex-start;
          padding: 0.75rem;
        }

        /* Main Content */
        .main-content {
          flex: 1;
          margin-left: var(--sidebar-width);
          padding: var(--spacing-lg);
          min-height: 100vh;
        }

        /* Menu Overlay */
        .menu-overlay {
          display: none;
        }

        /* Responsive */
        @media (max-width: 767px) {
          .mobile-header {
            display: flex;
          }

          .main-content {
            margin-left: 0;
            padding: 1rem;
            padding-top: 80px;
          }

          .sidebar {
            transform: translateX(-100%);
            width: 280px;
            padding-top: 80px;
          }

          .sidebar.open {
            transform: translateX(0);
          }

          .menu-overlay {
            display: block;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 150;
          }

          .hide-mobile {
            display: none;
          }
        }

        @media (min-width: 768px) and (max-width: 1023px) {
          .main-content {
            padding: var(--spacing-md);
          }
        }
      `}</style>
    </div>
  );
};

const MenuItem = ({ to, icone, texto, onClick }) => (
  <NavLink 
    to={to} 
    className={({ isActive }) => isActive ? 'sidebar-item active' : 'sidebar-item'}
    onClick={onClick}
  >
    {icone}
    <span>{texto}</span>
  </NavLink>
);

export default Layout;