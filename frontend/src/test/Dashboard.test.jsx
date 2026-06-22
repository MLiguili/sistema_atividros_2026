import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import Dashboard from '../pages/Dashboard'

vi.mock('../api/config', () => ({
  default: {
    get: vi.fn(),
  },
}))

import api from '../api/config'

const mockData = {
  stats: { molduras: 10, vidros: 8, fundos: 5, suplementos: 3, pedidos: 20, clientes: 15, receita_total: 15000, ticket_medio: 750, taxa_conversao: 85 },
  grafico_vendas: [],
  grafico_producao: [],
  top_produtos: [],
  pedidos_hoje: [],
  alertas_estoque: [],
}

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.get.mockResolvedValue({ data: mockData })
  })

  it('shows loading state then renders dashboard', async () => {
    render(<Dashboard />)

    expect(screen.getByText('Carregando...')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('Molduras')).toBeInTheDocument()
    })
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('Vidros')).toBeInTheDocument()
    expect(screen.getByText('8')).toBeInTheDocument()
    expect(screen.getByText('Pedidos')).toBeInTheDocument()
    expect(screen.getByText('R$ 15000.00')).toBeInTheDocument()
  })
})
