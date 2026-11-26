import React, { useState } from 'react';
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { useAutenticacao } from '../context/ContextoAutenticacao';
import Card from '../components/ui/Card';
import Field from '../components/ui/Field';
import Button from '../components/ui/Button';
import Callout from '../components/ui/Callout';

/**
 * Página de autenticação do sistema Atividros com estado controlado e feedback acessível.
 *
 * @returns {JSX.Element} Formulário de login ou redirecionamento para o Dashboard.
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
   * Submete as credenciais reais informadas no formulário para autenticação.
   *
   * @param {React.FormEvent<HTMLFormElement>} evento Evento de submit.
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
      } else if (err.response?.status === 400 || err.response?.status === 403) {
        setErro(err.response?.data?.detail || 'Usuário inativo.');
      } else {
        setErro('Não foi possível conectar ao servidor. Tente novamente.');
      }
    } finally {
      setEnviando(false);
    }
  };

  return (
    <main className="at-login-page">
      <Card className="at-login-card">
        <div style={{ textAlign: 'center', marginBottom: 'var(--at-space-5)' }}>
          <h1 style={{ fontSize: 'var(--at-font-2xl)' }}>Atividros</h1>
          <p className="at-muted">Acesse com seu usuário e senha internos</p>
        </div>

        {sessaoExpirada && (
          <Callout variant="warning" role="status">
            Sua sessão expirou. Faça login novamente para continuar.
          </Callout>
        )}

        {erro && (
          <Callout variant="danger" role="alert">
            {erro}
          </Callout>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <Field id="login-usuario" label="Usuário" required>
            <input
              id="login-usuario"
              className="at-input"
              type="text"
              autoComplete="username"
              required
              value={nomeUsuario}
              onChange={(e) => setNomeUsuario(e.target.value)}
              placeholder="Digite seu usuário"
              disabled={enviando}
            />
          </Field>

          <Field id="login-senha" label="Senha" required>
            <input
              id="login-senha"
              className="at-input"
              type="password"
              autoComplete="current-password"
              required
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              placeholder="Digite sua senha"
              disabled={enviando}
            />
          </Field>

          <Button type="submit" variant="primary" loading={enviando} style={{ width: '100%' }}>
            {enviando ? 'Entrando...' : 'Entrar'}
          </Button>
        </form>
      </Card>
    </main>
  );
};

export default Login;
