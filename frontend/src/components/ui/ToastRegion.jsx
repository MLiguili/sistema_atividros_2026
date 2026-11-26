import React from 'react';
import { X } from 'lucide-react';
import { useToast } from '../../context/ContextoToast';

/**
 * Região acessível (aria-live="polite") para renderização das notificações toast ativas.
 *
 * @returns {JSX.Element} Container fixo de toasts.
 */
const ToastRegion = () => {
  const { toasts, removerToast } = useToast();

  return (
    <div className="at-toast-region" aria-live="polite" aria-atomic="true">
      {toasts.map((toast) => (
        <div key={toast.id} className={`at-toast at-toast--${toast.tipo}`}>
          <span>{toast.mensagem}</span>
          <button
            type="button"
            className="at-btn at-btn--icon"
            onClick={() => removerToast(toast.id)}
            aria-label="Dispensar notificação"
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>
      ))}
    </div>
  );
};

export default ToastRegion;
