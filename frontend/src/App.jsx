import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ProvedorAutenticacao, useAutenticacao } from './context/ContextoAutenticacao';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Estoque from './pages/Estoque';
import Clientes from './pages/Clientes';
import Pedidos from './pages/Pedidos';
import Calculadora from './pages/Calculadora';

/**
 * Componente wrapper para proteger rotas que exigem usuário autenticado.
 *
 * @param {{ children: React.ReactNode }} props Conteúdo protegido.
 * @returns {JSX.Element} Conteúdo autenticado ou redirecionamento para login.
 */
const RotaProtegida = ({ children }) => {
  const { usuario, carregando } = useAutenticacao();
  if (carregando) return <div>Carregando...</div>;
  if (!usuario) return <Navigate to="/login" replace />;
  return <div className="container" style={{ paddingTop: '2rem' }}>{children}</div>;
};

/**
 * Componente raiz da aplicação Atividros com configuração de rotas.
 *
 * @returns {JSX.Element} Árvore principal de roteamento e provedor de autenticação.
 */
function App() {
  return (
    <ProvedorAutenticacao>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<RotaProtegida><Layout><Dashboard /></Layout></RotaProtegida>} />
          <Route path="/estoque" element={<RotaProtegida><Layout><Estoque /></Layout></RotaProtegida>} />
          <Route path="/clientes" element={<RotaProtegida><Layout><Clientes /></Layout></RotaProtegida>} />
          <Route path="/pedidos" element={<RotaProtegida><Layout><Pedidos /></Layout></RotaProtegida>} />
          <Route path="/calculadora" element={<RotaProtegida><Layout><Calculadora /></Layout></RotaProtegida>} />
        </Routes>
      </Router>
    </ProvedorAutenticacao>
  );
}

export default App;
