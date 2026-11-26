import React, { useEffect, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  Box,
  Calculator,
  LayoutDashboard,
  LogOut,
  Menu,
  ShoppingCart,
  Tags,
  Users,
  X,
} from 'lucide-react';
import { useAutenticacao } from '../context/ContextoAutenticacao';
import Button from './ui/Button';

/**
 * Item de navegação lateral com fechamento automático do drawer mobile.
 *
 * @param {{ to: string, icon: React.ReactNode, label: string, onSelect: () => void }} props Propriedades.
 * @returns {JSX.Element} Link de navegação.
 */
const NavItem = ({ to, icon, label, onSelect }) => (
  <NavLink
    to={to}
    end={to === '/'}
    onClick={onSelect}
    className={({ isActive }) => `at-nav-link ${isActive ? 'active' : ''}`.trim()}
  >
    {icon}
    <span>{label}</span>
  </NavLink>
);

/**
 * Shell principal do aplicativo com navegação lateral responsiva (Balcão + Oficina).
 *
 * @param {{ children: React.ReactNode }} props Conteúdo da rota ativa.
 * @returns {JSX.Element} Layout completo da aplicação.
 */
const Layout = ({ children }) => {
  const { usuario, logout } = useAutenticacao();
  const navegar = useNavigate();
  const [menuAberto, setMenuAberto] = useState(false);

  useEffect(() => {
    const aoPressionarEsc = (evento) => {
      if (evento.key === 'Escape') setMenuAberto(false);
    };
    window.addEventListener('keydown', aoPressionarEsc);
    return () => window.removeEventListener('keydown', aoPressionarEsc);
  }, []);

  const handleLogout = () => {
    logout();
    navegar('/login');
  };

  return (
    <div className="at-app">
      <header className="at-mobile-header">
        <Button
          variant="icon"
          onClick={() => setMenuAberto((v) => !v)}
          aria-expanded={menuAberto}
          aria-controls="at-sidebar-nav"
          aria-label={menuAberto ? 'Fechar menu' : 'Abrir menu'}
        >
          {menuAberto ? <X size={22} aria-hidden="true" /> : <Menu size={22} aria-hidden="true" />}
        </Button>
        <span className="at-brand">ATIVIDROS</span>
        <div style={{ width: '44px' }} aria-hidden="true" />
      </header>

      {menuAberto && <div className="at-scrim" onClick={() => setMenuAberto(false)} aria-hidden="true" />}

      <aside id="at-sidebar-nav" className={`at-sidebar ${menuAberto ? 'at-sidebar--open' : ''}`.trim()}>
        <div className="at-sidebar__header">
          <span className="at-brand">ATIVIDROS</span>
          <span className="at-brand-sub">Sistema de Gestão V1.0</span>
        </div>

        <nav className="at-sidebar__nav" aria-label="Menu principal">
          <NavItem to="/" icon={<LayoutDashboard size={18} aria-hidden="true" />} label="Dashboard" onSelect={() => setMenuAberto(false)} />
          <NavItem to="/pedidos" icon={<ShoppingCart size={18} aria-hidden="true" />} label="Pedidos" onSelect={() => setMenuAberto(false)} />
          <NavItem to="/calculadora" icon={<Calculator size={18} aria-hidden="true" />} label="Calculadora" onSelect={() => setMenuAberto(false)} />
          <NavItem to="/estoque" icon={<Box size={18} aria-hidden="true" />} label="Estoque" onSelect={() => setMenuAberto(false)} />
          <NavItem to="/precos" icon={<Tags size={18} aria-hidden="true" />} label="Tabelas de Preço" onSelect={() => setMenuAberto(false)} />
          <NavItem to="/clientes" icon={<Users size={18} aria-hidden="true" />} label="Clientes" onSelect={() => setMenuAberto(false)} />
        </nav>

        <div className="at-sidebar__footer">
          <div className="at-user-chip">
            <div className="at-user-avatar" aria-hidden="true">
              {usuario?.nome_usuario?.[0]?.toUpperCase() || 'A'}
            </div>
            <div>
              <p className="at-user-name">{usuario?.nome_completo || usuario?.nome_usuario || 'Operador'}</p>
              <p className="at-user-role">Loja Atividros</p>
            </div>
          </div>
          <Button variant="secondary" size="sm" onClick={handleLogout}>
            <LogOut size={16} aria-hidden="true" />
            <span>Sair</span>
          </Button>
        </div>
      </aside>

      <main className="at-main">
        <div className="at-container">{children}</div>
      </main>
    </div>
  );
};

export default Layout;
