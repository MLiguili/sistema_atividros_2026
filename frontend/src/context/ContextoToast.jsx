import React, { createContext, useCallback, useContext, useState } from 'react';

const ContextoToast = createContext(null);

/**
 * Provedor global de notificações transitórias (Toasts) com remoção automática após 6 segundos.
 *
 * @param {{ children: React.ReactNode }} props Componentes filhos.
 * @returns {JSX.Element} Provedor de toasts.
 */
export const ProvedorToast = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const removerToast = useCallback((id) => {
    setToasts((atual) => atual.filter((item) => item.id !== id));
  }, []);

  const notificar = useCallback(
    (mensagem, tipo = 'success') => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
      setToasts((atual) => [...atual, { id, mensagem, tipo }]);
      setTimeout(() => removerToast(id), 6000);
    },
    [removerToast],
  );

  return (
    <ContextoToast.Provider value={{ toasts, notificar, removerToast }}>
      {children}
    </ContextoToast.Provider>
  );
};

/**
 * Hook para disparar notificações toast em qualquer página ou componente.
 *
 * @returns {{ toasts: Array, notificar: Function, removerToast: Function }} Estado e ações de toast.
 */
export const useToast = () => {
  const ctx = useContext(ContextoToast);
  if (!ctx) {
    return { toasts: [], notificar: () => {}, removerToast: () => {} };
  }
  return ctx;
};
