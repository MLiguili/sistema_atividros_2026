import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import KanbanBoard, { COLUNAS_KANBAN } from '../components/pedidos/KanbanBoard';

describe('KanbanBoard', () => {
  it('renderiza exatamente 6 colunas operacionais sem coluna Entregue e exibe apenas confirmados', async () => {
    const user = userEvent.setup();
    expect(COLUNAS_KANBAN.map((c) => c.key)).toEqual([
      'pendente',
      'aguardando_material',
      'na_fila',
      'em_producao',
      'embalando',
      'pronto_entrega',
    ]);

    const pedidos = [
      {
        id: 1,
        numero_pedido: 'PED-CONFIRMADO',
        status_geral: 'confirmado',
        status_producao: 'na_fila',
        status_financeiro: 'sem_pagamento',
        valor_total: 250,
        saldo_devedor: 250,
        cliente: { nome: 'Maria' },
      },
      {
        id: 2,
        numero_pedido: 'PED-RASCUNHO',
        status_geral: 'rascunho',
        status_producao: 'pendente',
        status_financeiro: 'sem_pagamento',
        valor_total: 100,
        saldo_devedor: 100,
        cliente: { nome: 'João' },
      },
      {
        id: 3,
        numero_pedido: 'PED-ENTREGUE',
        status_geral: 'entregue',
        status_producao: 'pronto_entrega',
        status_financeiro: 'pago_total',
        valor_total: 400,
        saldo_devedor: 0,
        cliente: { nome: 'Carlos' },
      },
    ];

    render(
      <KanbanBoard
        pedidos={pedidos}
        onAbrirDetalhe={vi.fn()}
        onAbrirBaixa={vi.fn()}
        onAvancarProducao={vi.fn()}
        onMarcarEntregue={vi.fn()}
      />,
    );

    expect(screen.getByText('PED-CONFIRMADO')).toBeInTheDocument();
    expect(screen.queryByText('PED-RASCUNHO')).not.toBeInTheDocument();
    expect(screen.queryByText('PED-ENTREGUE')).not.toBeInTheDocument();
    expect(screen.queryByRole('region', { name: /Coluna Entregue/i })).not.toBeInTheDocument();

    const tabNaFila = screen.getByRole('tab', { name: /Na Fila \(1\)/i });
    await user.click(tabNaFila);
    expect(tabNaFila).toHaveAttribute('aria-selected', 'true');
  });
});
