import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../api/config';

const ContextoAutenticacao = createContext();

/**
 * Provedor de contexto responsável pelo estado global de autenticação do usuário.
 *
 * @param {{ children: React.ReactNode }} props Componentes filhos.
 * @returns {JSX.Element} Provedor de autenticação.
 */
export const ProvedorAutenticacao = ({ children }) => {
  const [usuario, setUsuario] = useState(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    /**
     * Carrega o usuário autenticado caso haja token armazenado no navegador.
     *
     * @returns {Promise<void>}
     */
    const carregarUsuario = async () => {
      const token = localStorage.getItem('token_atividros');
      if (token) {
        try {
          const resposta = await api.get('/autenticacao/me');
          setUsuario(resposta.data);
        } catch (erro) {
          console.error('Falha ao autenticar token:', erro);
          localStorage.removeItem('token_atividros');
        }
      }
      setCarregando(false);
    };

    /**
     * Limpa o estado do usuário quando o interceptor detecta sessão expirada.
     */
    const aoExpirarSessao = () => {
      setUsuario(null);
    };

    window.addEventListener('atividros:sessao-expirada', aoExpirarSessao);
    carregarUsuario();

    return () => {
      window.removeEventListener('atividros:sessao-expirada', aoExpirarSessao);
    };
  }, []);

  /**
   * Realiza autenticação via OAuth2 form-urlencoded e carrega o perfil do usuário.
   *
   * @param {string} nomeUsuario Nome de usuário.
   * @param {string} senha Senha em texto plano.
   * @returns {Promise<object>} Dados do usuário autenticado.
   */
  const login = async (nomeUsuario, senha) => {
    const dados = new URLSearchParams();
    dados.append('username', nomeUsuario);
    dados.append('password', senha);

    const resposta = await api.post('/autenticacao/entrar', dados, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });

    const { token_acesso } = resposta.data;
    localStorage.setItem('token_atividros', token_acesso);

    const infoUsuario = await api.get('/autenticacao/me');
    setUsuario(infoUsuario.data);
    return infoUsuario.data;
  };

  /**
   * Encerra a sessão local removendo o token JWT armazenado.
   */
  const logout = () => {
    localStorage.removeItem('token_atividros');
    setUsuario(null);
  };

  return (
    <ContextoAutenticacao.Provider value={{ usuario, login, logout, carregando }}>
      {children}
    </ContextoAutenticacao.Provider>
  );
};

/**
 * Hook utilitário para consumir o contexto de autenticação.
 *
 * @returns {{ usuario: object | null, login: Function, logout: Function, carregando: boolean }}
 */
export const useAutenticacao = () => useContext(ContextoAutenticacao);
