import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { ProvedorAutenticacao, useAutenticacao } from './context/ContextoAutenticacao';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Estoque from './pages/Estoque';
import Clientes from './pages/Clientes';
import Pedidos from './pages/Pedidos';
import Calculadora from './pages/Calculadora';

const Login = () => {
  const { login } = useAutenticacao();
  const navigate = useNavigate();
  const handleSubmit = (e) => {
    e.preventDefault();
    login('admin', 'admin123')
      .then(() => navigate('/'))
      .catch(err => alert('Erro no login: ' + err.message));
  };
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <div className="card" style={{ width: '100%', maxWidth: '400px' }}>
        <h2 style={{ textAlign: 'center' }}>Atividros Login</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Usuário</label>
            <input className="input-control" type="text" required defaultValue="admin" />
          </div>
          <div className="form-group">
            <label>Senha</label>
            <input className="input-control" type="password" required defaultValue="admin123" />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>Entrar</button>
        </form>
      </div>
    </div>
  );
};

const RotaProtegida = ({ children }) => {
  const { usuario, carregando } = useAutenticacao();
  if (carregando) return <div>Carregando...</div>;
  if (!usuario) return <Navigate to="/login" />;
  return <div className="container" style={{ paddingTop: '2rem' }}>{children}</div>;
};

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
          {/* Rotas futuras: Estoque, Pedidos, etc. */}
        </Routes>
      </Router>
    </ProvedorAutenticacao>
  );
}

export default App;
