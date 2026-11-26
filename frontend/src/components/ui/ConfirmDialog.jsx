import React, { useEffect, useRef } from 'react';
import Dialog from './Dialog';
import Button from './Button';

/**
 * Diálogo de confirmação para ações destrutivas com foco inicial seguro no botão Cancelar (DD-010).
 *
 * @param {{
 *   open: boolean,
 *   onClose: () => void,
 *   onConfirm: () => void,
 *   title: string,
 *   confirmLabel: string,
 *   cancelLabel?: string,
 *   loading?: boolean,
 *   children: React.ReactNode
 * }} props Propriedades do ConfirmDialog.
 * @returns {JSX.Element | null} Diálogo de confirmação acessível.
 */
const ConfirmDialog = ({
  open,
  onClose,
  onConfirm,
  title,
  confirmLabel,
  cancelLabel = 'Cancelar',
  loading = false,
  children,
}) => {
  const cancelBtnRef = useRef(null);

  useEffect(() => {
    if (open && cancelBtnRef.current) {
      cancelBtnRef.current.focus();
    }
  }, [open]);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={title}
      size="sm"
      closeOnBackdrop={false}
      footer={
        <>
          <button
            ref={cancelBtnRef}
            type="button"
            className="at-btn at-btn--secondary"
            onClick={onClose}
            disabled={loading}
          >
            {cancelLabel}
          </button>
          <Button variant="danger" onClick={onConfirm} loading={loading}>
            {confirmLabel}
          </Button>
        </>
      }
    >
      {children}
    </Dialog>
  );
};

export default ConfirmDialog;
