import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import PedidoLista from '../components/pedidos/PedidoLista';

describe('PedidoLista', () => {
  it('renderiza pedidos e orçamentos na tabela e filtra por status geral', async () => {
    const user = userEvent.setup();
    const onChangeFiltroGeral = vi.fn();

    const pedidos = [
      {
        id: 1,
        numero_pedido: '202600001',
        criado_em: '2026-11-26T10:00:00Z',
        prazo_entrega: '2026-12-01',
        status_geral: 'rascunho',
        status_producao: 'pendente',
        status_financeiro: 'sem_pagamento',
        valor_total: 250,
        saldo_devedor: 250,
        cliente: { nome: 'Marina' },
      },
      {
        id: 2,
        numero_pedido: '202600002',
        criado_em: '2026-11-26T11:00:00Z',
        prazo_entrega: '2026-12-03',
        status_geral: 'confirmado',
        status_producao: 'na_fila',
        status_financeiro: 'pago_total',
        valor_total: 500,
        saldo_devedor: 0,
        cliente: { nome: 'Galeria' },
      },
    ];

    render(
      <PedidoLista
        pedidos={pedidos}
        filtroGeral=""
        onChangeFiltroGeral={onChangeFiltroGeral}
        onAbrirDetalhe={vi.fn()}
        onEditarRascunho={vi.fn()}
        onBaixarPdf={vi.fn()}
      />,
    );

    expect(screen.getByText('202600001')).toBeInTheDocument();
    expect(screen.getByText('202600002')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /editar/i })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /orçamentos \(rascunho\)/i }));
    expect(onChangeFiltroGeral).toHaveBeenCalledWith('rascunho');
  });
});
