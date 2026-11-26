import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import api from '../api/config';
import ModalBaixaEstoque from '../components/pedidos/ModalBaixaEstoque';

vi.mock('../api/config', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('ModalBaixaEstoque', () => {
  it('ajusta barras com stepper, exibe alerta não bloqueante em ruptura e envia baixa-estoque', async () => {
    const user = userEvent.setup();
    const onConfirmado = vi.fn();

    api.get.mockResolvedValueOnce({
      data: {
        possui_insumos_estoque: true,
        molduras: [
          {
            moldura_id: 7,
            codigo: 'MLD-001',
            cor: 'Preto',
            barras_sugeridas: 1,
            estoque_atual_barras: 1,
            saldo_projetado: 0,
            em_ruptura: false,
          },
        ],
        vidros: [],
        fundos: [],
        materiais_para_compra: ["Fundo 'Foam Board' (0.4000 m²) não cadastrado no estoque — precisa ser comprado."],
      },
    });
    api.post.mockResolvedValueOnce({
      data: {
        pedido: { id: 10, numero_pedido: 'PED-2026-0001' },
        materiais_baixados: [],
        alertas_ruptura: ['Moldura MLD-001 ficou negativa (-1)'],
      },
    });

    render(
      <ModalBaixaEstoque
        open
        onClose={() => {}}
        pedido={{ id: 10, numero_pedido: 'PED-2026-0001' }}
        onConfirmado={onConfirmado}
      />,
    );

    expect(await screen.findByText(/MLD-001 — Preto/)).toBeInTheDocument();
    expect(screen.getByText(/compra de material necessária/i)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /aumentar barras de MLD-001/i }));

    expect(await screen.findByText(/ruptura de estoque projetada/i)).toBeInTheDocument();
    const confirmBtn = screen.getByRole('button', { name: /confirmar baixa e iniciar produção/i });
    expect(confirmBtn).toBeEnabled();

    await user.click(confirmBtn);
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/pedidos/10/baixa-estoque', {
        ajustes_molduras: [{ moldura_id: 7, barras_baixadas: 2 }],
        observacao: null,
      });
      expect(onConfirmado).toHaveBeenCalled();
    });
  });
});
