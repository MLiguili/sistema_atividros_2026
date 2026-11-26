import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import ConfirmDialog from '../components/ui/ConfirmDialog';

describe('ConfirmDialog', () => {
  it('foca inicialmente no botão Cancelar por segurança e chama onConfirm ao confirmar', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    const onClose = vi.fn();

    render(
      <ConfirmDialog
        open
        onClose={onClose}
        onConfirm={onConfirm}
        title="Excluir pedido?"
        confirmLabel="Excluir"
      >
        <p>Confirma exclusão?</p>
      </ConfirmDialog>,
    );

    const cancelBtn = screen.getByRole('button', { name: 'Cancelar' });
    expect(cancelBtn).toHaveFocus();

    await user.click(screen.getByRole('button', { name: 'Excluir' }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });
});
