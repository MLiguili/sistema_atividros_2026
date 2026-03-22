import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../api/config';

const ContextoAutenticacao = createContext();

export const ProvedorAutenticacao = ({ children }) => {
  const [usuario, setUsuario] = useState(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
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
    carregarUsuario();
  }, []);

  const login = async (nome_usuario, senha) => {
    const dados = new URLSearchParams();
    dados.append('username', nome_usuario);
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

export const useAutenticacao = () => useContext(ContextoAutenticacao);
