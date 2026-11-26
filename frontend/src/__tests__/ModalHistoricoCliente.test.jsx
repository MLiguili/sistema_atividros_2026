import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import api from '../api/config';
import ModalHistoricoCliente from '../components/clientes/ModalHistoricoCliente';

vi.mock('../api/config', () => ({
  default: {
    get: vi.fn(),
  },
}));

describe('ModalHistoricoCliente', () => {
  it('permite clicar em um pedido antigo para ver itens, pagamentos e eventos e voltar ao histórico', async () => {
    const user = userEvent.setup();

    api.get.mockResolvedValueOnce({
      data: [
        {
          id: 8,
          numero_pedido: '202600008',
          criado_em: '2026-11-26T10:00:00Z',
          valor_total: 303.94,
          status_geral: 'entregue',
          status_producao: 'pronto_entrega',
          status_financeiro: 'pago_total',
        },
      ],
    });

    api.get.mockResolvedValueOnce({
      data: {
        id: 8,
        numero_pedido: '202600008',
        criado_em: '2026-11-26T10:00:00Z',
        data_validade_orcamento: '2026-12-03',
        prazo_entrega: '2026-11-25',
        endereco_entrega: 'Retirada no balcão',
        observacoes: 'Entregue sem pendências',
        subtotal_itens: 303.94,
        frete: 0,
        desconto_valor: 0,
        desconto_tipo: 'valor',
        valor_total: 303.94,
        valor_pago: 303.94,
        saldo_devedor: 0,
        status_geral: 'entregue',
        status_producao: 'pronto_entrega',
        status_financeiro: 'pago_total',
        itens: [
          {
            id: 1,
            quantidade: 1,
            descricao: 'Quadro 35x45cm Freijó',
            preco_unitario: 303.94,
            subtotal: 303.94,
            molduras: [
              {
                codigo_moldura_snapshot: 'MLD-FREIJO-3CM',
                largura_calculada_cm: 41,
                altura_calculada_cm: 51,
                metragem_total_m: 1.84,
                barras_sugeridas: 1,
              },
            ],
          },
        ],
        pagamentos: [
          {
            id: 10,
            valor: 303.94,
            forma_pagamento: 'pix',
            data_pagamento: '2026-11-26T10:05:00Z',
            estornado: false,
            observacao: 'Quitação integral',
          },
        ],
        eventos: [
          {
            id: 99,
            eixo: 'geral',
            status_anterior: 'confirmado',
            status_novo: 'entregue',
            observacao: 'Retirado pelo cliente',
            criado_em: '2026-11-26T12:00:00Z',
          },
        ],
      },
    });

    render(
      <MemoryRouter>
        <ModalHistoricoCliente
          cliente={{ id: 4, nome: 'Studio', sobrenome: 'Vértice' }}
          onClose={vi.fn()}
        />
      </MemoryRouter>,
    );

    const cardPedido = await screen.findByRole('button', { name: /#202600008/i });
    await user.click(cardPedido);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/pedidos/8');
    });

    expect(await screen.findByText(/1× Quadro 35x45cm Freijó/i)).toBeInTheDocument();
    expect(screen.getByText(/Quitação integral/i)).toBeInTheDocument();
    expect(screen.getByText(/Retirado pelo cliente/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /voltar ao histórico/i }));
    expect(await screen.findByText(/Ver detalhes/i)).toBeInTheDocument();
  });
});
