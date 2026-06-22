import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import Financeiro from '../pages/Financeiro'

vi.mock('../api/config', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import api from '../api/config'

describe('Financeiro', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.get.mockImplementation((url) => {
      if (url === '/financeiro/resumo') return Promise.resolve({
        data: {
          total_a_receber: 0, total_recebido: 0, total_a_pagar: 0, total_pago: 0,
          saldo_previsto: 0, contas_receber_vencidas: 0, contas_pagar_vencidas: 0,
        },
      })
      return Promise.resolve({ data: [] })
    })
  })

  it('renders financeiro page with tabs', async () => {
    render(
      <BrowserRouter>
        <Financeiro />
      </BrowserRouter>
    )
    await waitFor(() => {
      expect(screen.getByText('A Receber')).toBeInTheDocument()
      expect(screen.getByText('A Pagar')).toBeInTheDocument()
      expect(screen.getByText('Fluxo de Caixa')).toBeInTheDocument()
    })
  })
})
