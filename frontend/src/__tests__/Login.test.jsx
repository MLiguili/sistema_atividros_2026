import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import Login from '../pages/Login';

const mockLogin = vi.fn();

vi.mock('../context/ContextoAutenticacao', () => ({
  useAutenticacao: () => ({
    usuario: null,
    login: mockLogin,
  }),
}));

describe('Login page', () => {
  it('exibe aviso de sessão expirada quando query string sessao=expirada', () => {
    render(
      <MemoryRouter initialEntries={['/login?sessao=expirada']}>
        <Login />
      </MemoryRouter>,
    );
    expect(screen.getByText(/sua sessão expirou/i)).toBeInTheDocument();
  });

  it('submete usuário e senha ao clicar em Entrar e exibe erro quando falha', async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValueOnce({ response: { status: 401, data: { detail: 'Credenciais inválidas' } } });

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Login />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText(/usuário/i), 'admin');
    await user.type(screen.getByLabelText(/senha/i), 'errada');
    await user.click(screen.getByRole('button', { name: /entrar/i }));

    expect(mockLogin).toHaveBeenCalledWith('admin', 'errada');
    expect(await screen.findByText(/usuário ou senha inválidos/i)).toBeInTheDocument();
  });
});
