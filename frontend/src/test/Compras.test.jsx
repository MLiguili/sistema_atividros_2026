import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import Compras from '../pages/Compras'

vi.mock('../api/config', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}))

import api from '../api/config'

describe('Compras', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.get.mockResolvedValue({ data: [] })
  })

  it('renders the compras page with tabs', async () => {
    render(
      <BrowserRouter>
        <Compras />
      </BrowserRouter>
    )
    await waitFor(() => {
      expect(screen.getByText('Fornecedores')).toBeInTheDocument()
      expect(screen.getByText('Ordens de Compra')).toBeInTheDocument()
      expect(screen.getByText('Sugestões')).toBeInTheDocument()
    })
  })
})
