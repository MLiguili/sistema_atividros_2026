import React, { useState } from 'react';
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { useAutenticacao } from '../context/ContextoAutenticacao';

/**
 * Página de autenticação do sistema Atividros.
 * Controla credenciais reais via estado React e exibe feedback acessível inline.
 *
 * @returns {JSX.Element} Formulário de login ou redirecionamento para o painel.
 */
const Login = () => {
  const { usuario, login } = useAutenticacao();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [nomeUsuario, setNomeUsuario] = useState('');
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState('');
  const [enviando, setEnviando] = useState(false);

  const sessaoExpirada = searchParams.get('sessao') === 'expirada';

  if (usuario) {
    return <Navigate to="/" replace />;
  }

  /**
   * Submete as credenciais informadas pelo usuário para autenticação.
   *
   * @param {React.FormEvent<HTMLFormElement>} evento Evento de envio do formulário.
   * @returns {Promise<void>}
   */
  const handleSubmit = async (evento) => {
    evento.preventDefault();
    setErro('');

    const usuarioLimpo = nomeUsuario.trim();
    if (!usuarioLimpo || !senha) {
      setErro('Informe usuário e senha para entrar.');
      return;
    }

    setEnviando(true);
    try {
      await login(usuarioLimpo, senha);
      navigate('/', { replace: true });
    } catch (err) {
      if (err.response?.status === 401) {
        setErro('Usuário ou senha inválidos.');
      } else if (err.response?.status === 400) {
        setErro(err.response?.data?.detail || 'Usuário inativo.');
      } else {
        setErro('Não foi possível conectar ao servidor. Tente novamente.');
      }
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', padding: '1rem' }}>
      <div className="card" style={{ width: '100%', maxWidth: '400px' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '1.5rem' }}>Atividros Login</h2>

        {sessaoExpirada && (
          <div
            role="status"
            style={{
              marginBottom: '1rem',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              background: 'rgba(245, 158, 11, 0.15)',
              border: '1px solid rgba(245, 158, 11, 0.4)',
              color: '#fcd34d',
              fontSize: '0.875rem',
            }}
          >
            Sua sessão expirou. Faça login novamente para continuar.
          </div>
        )}

        {erro && (
          <div
            role="alert"
            style={{
              marginBottom: '1rem',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.4)',
              color: '#fca5a5',
              fontSize: '0.875rem',
            }}
          >
            {erro}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="login-usuario">Usuário</label>
            <input
              id="login-usuario"
              className="input-control"
              type="text"
              autoComplete="username"
              required
              value={nomeUsuario}
              onChange={(e) => setNomeUsuario(e.target.value)}
              placeholder="Digite seu usuário"
              disabled={enviando}
            />
          </div>
          <div className="form-group">
            <label htmlFor="login-senha">Senha</label>
            <input
              id="login-senha"
              className="input-control"
              type="password"
              autoComplete="current-password"
              required
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              placeholder="Digite sua senha"
              disabled={enviando}
            />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={enviando}>
            {enviando ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
