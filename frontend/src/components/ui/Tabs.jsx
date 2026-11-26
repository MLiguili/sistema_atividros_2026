import React, { useRef } from 'react';

/**
 * Componente de abas acessíveis com navegação por setas (roving tabindex).
 *
 * @param {{
 *   tabs: Array<{ id: string, label: string }>,
 *   activeId: string,
 *   onChange: (id: string) => void,
 *   ariaLabel?: string
 * }} props Propriedades de Tabs.
 * @returns {JSX.Element} Barra de abas acessível.
 */
const Tabs = ({ tabs, activeId, onChange, ariaLabel = 'Seções' }) => {
  const btnRefs = useRef([]);

  const handleKeyDown = (evento, index) => {
    if (evento.key !== 'ArrowRight' && evento.key !== 'ArrowLeft') return;
    evento.preventDefault();
    const delta = evento.key === 'ArrowRight' ? 1 : -1;
    const nextIndex = (index + delta + tabs.length) % tabs.length;
    onChange(tabs[nextIndex].id);
    btnRefs.current[nextIndex]?.focus();
  };

  return (
    <div className="at-tabs" role="tablist" aria-label={ariaLabel}>
      {tabs.map((tab, index) => {
        const ativa = tab.id === activeId;
        return (
          <button
            key={tab.id}
            ref={(el) => {
              btnRefs.current[index] = el;
            }}
            type="button"
            role="tab"
            aria-selected={ativa}
            tabIndex={ativa ? 0 : -1}
            className={`at-tab ${ativa ? 'at-tab--active' : ''}`.trim()}
            onClick={() => onChange(tab.id)}
            onKeyDown={(e) => handleKeyDown(e, index)}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
};

export default Tabs;
