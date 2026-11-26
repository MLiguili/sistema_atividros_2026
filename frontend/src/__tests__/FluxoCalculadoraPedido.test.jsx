import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import api from '../api/config';
import Calculadora from '../pages/Calculadora';
import PedidoForm from '../components/pedidos/PedidoForm';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock('../api/config', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

describe('Fluxo Calculadora -> PedidoForm com alerta de preço abaixo do sugerido', () => {
  it('calcula na Calculadora, navega para /pedidos e alerta quando preço praticado fica abaixo do sugerido', async () => {
    const user = userEvent.setup();

    api.get.mockResolvedValue({ data: [] });
    api.post.mockResolvedValueOnce({
      data: {
        descricao_sugerida: 'Quadro 50x40cm com Vidro incolor',
        valor_sugerido_unitario: 150,
        total_sugerido: 150,
        dimensoes: {
          obra: { largura: 50, altura: 40 },
          vidro: { largura: 50, altura: 40 },
          molduras: [],
          quadro_final: { largura: 50, altura: 40 },
        },
        areas: { area_real_m2: 0.2, area_cobrada_vidro_m2: 0.25 },
        custos: [{ nome: 'Vidro incolor', medida: 0.25, unidade: 'm²', subtotal: 50 }],
      },
    });

    render(
      <MemoryRouter>
        <Calculadora />
      </MemoryRouter>,
    );

    expect(screen.queryByLabelText(/chapa física no estoque/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/chapa de fundo no estoque/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /calcular orçamento/i }));
    expect(await screen.findByText(/unitário sugerido:/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /adicionar ao pedido/i }));
    expect(mockNavigate).toHaveBeenCalledWith(
      '/pedidos',
      expect.objectContaining({
        state: expect.objectContaining({
          itemCalculadora: expect.objectContaining({
            valor_sugerido: 150,
            preco_unitario: 150,
          }),
        }),
      }),
    );

    const itemRecebido = mockNavigate.mock.calls[0][1].state.itemCalculadora;

    render(
      <PedidoForm
        open
        onClose={() => {}}
        itemInicialCalculadora={itemRecebido}
        clientes={[{ id: 1, nome: 'Cliente Teste', telefone: '1199999999' }]}
        onClienteCriado={() => {}}
        catalogos={{ molduras: [], vidros: [], fundos: [], tabelaVidro: [], tabelaFundo: [], tabelaPaspatour: [] }}
        onSalvo={() => {}}
      />,
    );

    const precoInput = screen.getByLabelText(/preço unit\. praticado/i);
    await user.clear(precoInput);
    await user.type(precoInput, '100');

    expect(screen.getByText(/abaixo do valor sugerido/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /criar orçamento/i })).toBeEnabled();
  });
});
