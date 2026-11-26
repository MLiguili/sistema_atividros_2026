import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import Button from './Button';

/**
 * Modal acessível baseado em <dialog>.showModal() nativo com trap de foco e fechamento por Esc.
 *
 * @param {{
 *   open: boolean,
 *   onClose: () => void,
 *   title: string,
 *   size?: 'sm' | 'md' | 'lg',
 *   closeOnBackdrop?: boolean,
 *   footer?: React.ReactNode,
 *   children: React.ReactNode
 * }} props Propriedades do diálogo.
 * @returns {JSX.Element | null} Diálogo modal.
 */
const Dialog = ({
  open,
  onClose,
  title,
  size = 'md',
  closeOnBackdrop = true,
  footer = null,
  children,
}) => {
  const dialogRef = useRef(null);
  const titleId = React.useId();

  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;

    if (open && !el.open) {
      el.showModal();
    } else if (!open && el.open) {
      el.close();
    }
  }, [open]);

  if (!open) return null;

  const handleCancel = (evento) => {
    evento.preventDefault();
    onClose();
  };

  const handleBackdropClick = (evento) => {
    if (closeOnBackdrop && evento.target === dialogRef.current) {
      onClose();
    }
  };

  const sizeClass = size === 'sm' ? 'at-dialog--sm' : size === 'lg' ? 'at-dialog--lg' : '';

  return (
    <dialog
      ref={dialogRef}
      className={`at-dialog ${sizeClass}`.trim()}
      aria-labelledby={titleId}
      onCancel={handleCancel}
      onClick={handleBackdropClick}
    >
      <div className="at-dialog__inner">
        <header className="at-dialog__header">
          <h3 id={titleId}>{title}</h3>
          <Button variant="icon" onClick={onClose} aria-label="Fechar janela">
            <X size={18} aria-hidden="true" />
          </Button>
        </header>
        <div className="at-dialog__body">{children}</div>
        {footer && <footer className="at-dialog__footer">{footer}</footer>}
      </div>
    </dialog>
  );
};

export default Dialog;
