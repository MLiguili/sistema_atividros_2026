import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import Producao from '../pages/Producao'

vi.mock('../api/config', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import api from '../api/config'

const mockPedidos = [
  {
    id: 1,
    numero_pedido: '202600001',
    status_producao: 'pendente',
    status_geral: 'rascunho',
    status_financeiro: 'sem_pagamento',
    valor_total: '150.00',
    cliente: { nome: 'João', sobrenome: 'Silva' },
    itens: [{ id: 1, descricao: 'Quadro', quantidade: 1 }],
    criado_em: '2026-06-21T10:00:00Z',
  },
]

const mockResumo = {
  pendente: 1,
  aguardando_material: 0,
  em_producao: 0,
  para_embalar: 0,
  pronto_entrega: 0,
  entregue: 0,
  total: 1,
}

describe('Producao', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.get.mockImplementation((url) => {
      if (url === '/pedidos/') return Promise.resolve({ data: mockPedidos })
      if (url === '/producao/resumo') return Promise.resolve({ data: mockResumo })
      return Promise.reject(new Error('unknown'))
    })
  })

  it('renders production page title', async () => {
    render(
      <BrowserRouter>
        <Producao />
      </BrowserRouter>
    )
    await waitFor(() => {
      expect(screen.getByText('Produção')).toBeInTheDocument()
    })
  })

  it('shows pedido count in resumo', async () => {
    render(
      <BrowserRouter>
        <Producao />
      </BrowserRouter>
    )
    await waitFor(() => {
      const pendentes = screen.getAllByText('1')
      expect(pendentes.length).toBeGreaterThanOrEqual(1)
    })
  })
})
