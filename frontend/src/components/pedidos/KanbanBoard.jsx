import React, { useState } from 'react';
import { Columns3 } from 'lucide-react';
import PedidoCard from './PedidoCard';
import EmptyState from '../ui/EmptyState';

export const COLUNAS_KANBAN = [
  { key: 'pendente', label: 'Pendente' },
  { key: 'aguardando_material', label: 'Aguard. Material' },
  { key: 'na_fila', label: 'Na Fila' },
  { key: 'em_producao', label: 'Em Produção' },
  { key: 'embalando', label: 'Embalando' },
  { key: 'pronto_entrega', label: 'Pronto p/ Entrega' },
];

/**
 * Quadro Kanban de 6 colunas para pedidos exclusivamente confirmados em produção (DD-004).
 *
 * @param {{
 *   pedidos: Array<object>,
 *   onAbrirDetalhe: (p: object) => void,
 *   onAbrirBaixa: (p: object) => void,
 *   onAvancarProducao: (p: object, novoStatus: string) => void,
 *   onMarcarEntregue: (p: object) => void
 * }} props Propriedades do Kanban.
 * @returns {JSX.Element} Quadro Kanban responsivo com seletor de etapa mobile.
 */
const KanbanBoard = ({
  pedidos,
  onAbrirDetalhe,
  onAbrirBaixa,
  onAvancarProducao,
  onMarcarEntregue,
}) => {
  const [etapaMobile, setEtapaMobile] = useState('pendente');

  const pedidosConfirmados = pedidos.filter((p) => p.status_geral === 'confirmado');

  if (pedidosConfirmados.length === 0) {
    return (
      <EmptyState
        icon={<Columns3 size={40} aria-hidden="true" />}
        title="Nenhum pedido em produção"
        description="Pedidos confirmados aparecem automaticamente aqui para acompanhamento da oficina."
      />
    );
  }

  return (
    <div>
      <div className="at-kanban-mobile-tabs" role="tablist" aria-label="Etapas do Kanban">
        {COLUNAS_KANBAN.map((col) => {
          const qtd = pedidosConfirmados.filter((p) => p.status_producao === col.key).length;
          return (
            <button
              key={col.key}
              type="button"
              role="tab"
              aria-selected={etapaMobile === col.key}
              className={`at-tab ${etapaMobile === col.key ? 'at-tab--active' : ''}`}
              onClick={() => setEtapaMobile(col.key)}
            >
              {col.label} ({qtd})
            </button>
          );
        })}
      </div>

      <div className="at-kanban">
        {COLUNAS_KANBAN.map((col) => {
          const cards = pedidosConfirmados.filter((p) => p.status_producao === col.key);
          const ocultaMobile = etapaMobile !== col.key ? 'at-kanban__col--hidden-mobile' : '';

          return (
            <section
              key={col.key}
              className={`at-kanban__col ${ocultaMobile}`.trim()}
              aria-label={`Coluna ${col.label}`}
            >
              <header className="at-kanban__col-header">
                <h3>{col.label}</h3>
                <span className="at-badge at-num">{cards.length}</span>
              </header>

              <div className="at-kanban__cards">
                {cards.length === 0 ? (
                  <p className="at-muted" style={{ fontSize: 'var(--at-text-xs)', padding: 'var(--at-space-2) 0' }}>
                    Sem pedidos nesta etapa.
                  </p>
                ) : (
                  cards.map((pedido) => (
                    <PedidoCard
                      key={pedido.id}
                      pedido={pedido}
                      onAbrirDetalhe={onAbrirDetalhe}
                      onAbrirBaixa={onAbrirBaixa}
                      onAvancarProducao={onAvancarProducao}
                      onMarcarEntregue={onMarcarEntregue}
                    />
                  ))
                )}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
};

export default KanbanBoard;
