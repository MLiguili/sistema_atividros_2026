import React from 'react';
import { Eye, Hammer, PackageCheck, ArrowRight } from 'lucide-react';
import Button from '../ui/Button';
import StatusBadge from '../ui/StatusBadge';
import { formatarData, formatarMoeda } from '../../utils/formatadores';

/**
 * Cartão operacional enxuto de pedido exibido nas colunas do Kanban da oficina (DD-004).
 *
 * @param {{
 *   pedido: object,
 *   onAbrirDetalhe: (p: object) => void,
 *   onAbrirBaixa: (p: object) => void,
 *   onAvancarProducao: (p: object, novoStatus: string) => void,
 *   onMarcarEntregue: (p: object) => void
 * }} props Propriedades do cartão.
 * @returns {JSX.Element} Cartão de pedido.
 */
const PedidoCard = ({
  pedido,
  onAbrirDetalhe,
  onAbrirBaixa,
  onAvancarProducao,
  onMarcarEntregue,
}) => {
  const preProducao = ['pendente', 'aguardando_material', 'na_fila'].includes(pedido.status_producao);
  const saldoDevedor = Number(pedido.saldo_devedor || 0);

  return (
    <article className="at-pedido-card" aria-label={`Pedido ${pedido.numero_pedido}`}>
      <div className="at-pedido-card__top">
        <strong className="at-num">{pedido.numero_pedido}</strong>
        <span className="at-muted">
          {pedido.prazo_entrega ? `Prazo: ${formatarData(pedido.prazo_entrega)}` : 'Sem prazo'}
        </span>
      </div>

      <p style={{ fontWeight: 600 }}>
        {pedido.cliente?.nome || `Cliente #${pedido.cliente_id}`}
      </p>

      <div className="at-pedido-card__badges">
        <StatusBadge eixo="geral" status={pedido.status_geral} />
        <StatusBadge
          eixo="financeiro"
          status={pedido.status_financeiro}
          extraText={saldoDevedor > 0 ? `Falta ${formatarMoeda(saldoDevedor)}` : ''}
        />
      </div>

      <div className="at-pedido-card__footer">
        <span className="at-num" style={{ fontWeight: 700 }}>
          {formatarMoeda(pedido.valor_total)}
        </span>

        <div className="at-actions">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onAbrirDetalhe(pedido)}
            aria-label={`Detalhes de ${pedido.numero_pedido}`}
          >
            <Eye size={14} aria-hidden="true" /> Detalhes
          </Button>

          {preProducao && (
            <Button
              variant="primary"
              style={{ minHeight: 44 }}
              onClick={() => onAbrirBaixa(pedido)}
            >
              <Hammer size={14} aria-hidden="true" /> Baixar e Produzir
            </Button>
          )}

          {pedido.status_producao === 'em_producao' && (
            <Button
              variant="primary"
              style={{ minHeight: 44 }}
              onClick={() => onAvancarProducao(pedido, 'embalando')}
            >
              Embalar <ArrowRight size={14} aria-hidden="true" />
            </Button>
          )}

          {pedido.status_producao === 'embalando' && (
            <Button
              variant="primary"
              style={{ minHeight: 44 }}
              onClick={() => onAvancarProducao(pedido, 'pronto_entrega')}
            >
              Pronto <ArrowRight size={14} aria-hidden="true" />
            </Button>
          )}

          {pedido.status_producao === 'pronto_entrega' && (
            <Button
              variant="primary"
              style={{ minHeight: 44 }}
              onClick={() => onMarcarEntregue(pedido)}
            >
              <PackageCheck size={14} aria-hidden="true" /> Marcar Entregue
            </Button>
          )}
        </div>
      </div>
    </article>
  );
};

export default PedidoCard;
