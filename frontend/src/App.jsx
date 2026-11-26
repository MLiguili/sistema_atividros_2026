import React from 'react';
import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom';
import { ProvedorAutenticacao, useAutenticacao } from './context/ContextoAutenticacao';
import { ProvedorToast } from './context/ContextoToast';
import ToastRegion from './components/ui/ToastRegion';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Estoque from './pages/Estoque';
import TabelasPreco from './pages/TabelasPreco';
import Clientes from './pages/Clientes';
import Pedidos from './pages/Pedidos';
import Calculadora from './pages/Calculadora';

/**
 * Protege rotas autenticadas redirecionando visitantes não logados para /login.
 *
 * @param {{ children: React.ReactNode }} props Conteúdo protegido.
 * @returns {JSX.Element} Conteúdo autenticado ou redirecionamento.
 */
const RotaProtegida = ({ children }) => {
  const { usuario, carregando } = useAutenticacao();
  if (carregando) {
    return (
      <div className="at-state" role="status">
        Carregando sessão...
      </div>
    );
  }
  if (!usuario) return <Navigate to="/login" replace />;
  return children;
};

/**
 * Componente raiz do sistema Atividros configurando provedores, rotas e região de toasts.
 *
 * @returns {JSX.Element} Árvore principal da aplicação.
 */
function App() {
  return (
    <ProvedorAutenticacao>
      <ProvedorToast>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<RotaProtegida><Layout><Dashboard /></Layout></RotaProtegida>} />
            <Route path="/estoque" element={<RotaProtegida><Layout><Estoque /></Layout></RotaProtegida>} />
            <Route path="/precos" element={<RotaProtegida><Layout><TabelasPreco /></Layout></RotaProtegida>} />
            <Route path="/clientes" element={<RotaProtegida><Layout><Clientes /></Layout></RotaProtegida>} />
            <Route path="/pedidos" element={<RotaProtegida><Layout><Pedidos /></Layout></RotaProtegida>} />
            <Route path="/calculadora" element={<RotaProtegida><Layout><Calculadora /></Layout></RotaProtegida>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
        <ToastRegion />
      </ProvedorToast>
    </ProvedorAutenticacao>
  );
}

export default App;
