import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import api from '../api/config';
import TabelasPreco from '../pages/TabelasPreco';

vi.mock('../api/config', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('TabelasPreco', () => {
  it('exibe a aba Molduras carregando de /estoque/molduras e permite abrir modal de nova moldura', async () => {
    const user = userEvent.setup();

    api.get.mockResolvedValueOnce({
      data: [{ id: 1, tipo: 'incolor', descricao: 'Comum', preco_por_m2: 120, area_minima_m2: 0.25 }],
    });
    api.get.mockResolvedValueOnce({
      data: [
        {
          id: 9,
          codigo: 'MLD-TEST-01',
          cor: 'Preta',
          marca: 'Moldurarte',
          largura_barra: 3.0,
          tamanho_barra: 2.75,
          preco_custo: 30,
          preco_venda: 85,
        },
      ],
    });

    render(<TabelasPreco />);
    expect(await screen.findByText('Comum')).toBeInTheDocument();

    await user.click(screen.getByRole('tab', { name: /molduras/i }));
    expect(await screen.findByText('MLD-TEST-01')).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith('/estoque/molduras');

    await user.click(screen.getByRole('button', { name: /nova moldura/i }));
    expect(screen.getByLabelText(/preço de venda \(R\$\/m\)/i)).toBeInTheDocument();
  });
});
