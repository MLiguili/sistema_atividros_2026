import React, { useState } from 'react';
import {
  Archive,
  Ban,
  CheckCircle2,
  CircleDollarSign,
  Edit3,
  FileDown,
  Hammer,
  PackageCheck,
  Trash2,
} from 'lucide-react';
import Dialog from '../ui/Dialog';
import ConfirmDialog from '../ui/ConfirmDialog';
import Button from '../ui/Button';
import StatusBadge from '../ui/StatusBadge';
import Callout from '../ui/Callout';
import { formatarData, formatarMetragem, formatarMoeda } from '../../utils/formatadores';

/**
 * Painel modal de detalhe completo do pedido com controles dos 3 eixos, especificações de corte e timeline.
 *
 * @param {{
 *   open: boolean,
 *   onClose: () => void,
 *   pedido: object | null,
 *   onEditarRascunho: (p: object) => void,
 *   onAbrirBaixa: (p: object) => void,
 *   onAbrirPagamento: (p: object) => void,
 *   onMudarStatus: (p: object, eixo: 'geral' | 'producao', novoStatus: string) => Promise<void>,
 *   onBaixarPdf: (p: object) => Promise<void>,
 *   onExcluirPedido: (p: object) => Promise<void>
 * }} props Propriedades do detalhe.
 * @returns {JSX.Element | null} Modal de detalhe do pedido.
 */
const PedidoDetalhe = ({
  open,
  onClose,
  pedido,
  onEditarRascunho,
  onAbrirBaixa,
  onAbrirPagamento,
  onMudarStatus,
  onBaixarPdf,
  onExcluirPedido,
}) => {
  const [confirmCancelar, setConfirmCancelar] = useState(false);
  const [confirmExcluir, setConfirmExcluir] = useState(false);
  const [processando, setProcessando] = useState(false);

  if (!pedido) return null;

  const preProducao = ['pendente', 'aguardando_material', 'na_fila'].includes(pedido.status_producao);
  const podeExcluir =
    pedido.status_geral === 'rascunho' ||
    (pedido.status_geral === 'cancelado' && !(pedido.pagamentos || []).some((pg) => !pg.estornado));

  const executarMudanca = async (eixo, novoStatus) => {
    setProcessando(true);
    try {
      await onMudarStatus(pedido, eixo, novoStatus);
    } finally {
      setProcessando(false);
    }
  };

  return (
    <>
      <Dialog open={open} onClose={onClose} title={`Pedido ${pedido.numero_pedido}`} size="lg">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-4)' }}>
          <div className="at-actions">
            <StatusBadge eixo="geral" status={pedido.status_geral} />
            <StatusBadge eixo="producao" status={pedido.status_producao} />
            <StatusBadge eixo="financeiro" status={pedido.status_financeiro} />
          </div>

          {pedido.requer_estorno && (
            <Callout variant="warning">
              Pedido cancelado com pagamento ativo ({formatarMoeda(pedido.valor_pago)}). Abra Pagamentos para realizar o estorno.
            </Callout>
          )}

          {pedido.tem_item_abaixo_do_sugerido && (
            <Callout variant="warning">
              Este pedido contém item(ns) com preço praticado abaixo do valor sugerido pela calculadora.
            </Callout>
          )}

          <div className="at-grid-3">
            <div className="at-card">
              <div className="at-muted">Cliente</div>
              <strong>{pedido.cliente?.nome || `#${pedido.cliente_id}`}</strong>
              {pedido.cliente?.telefone && <div className="at-muted">{pedido.cliente.telefone}</div>}
            </div>
            <div className="at-card">
              <div className="at-muted">Datas</div>
              <div>Emissão: {formatarData(pedido.criado_em)}</div>
              <div>Prazo: {formatarData(pedido.prazo_entrega)}</div>
            </div>
            <div className="at-card">
              <div className="at-muted">Financeiro</div>
              <div className="at-num">Total: {formatarMoeda(pedido.valor_total)}</div>
              <div className="at-num">Devedor: {formatarMoeda(pedido.saldo_devedor)}</div>
            </div>
          </div>

          <section className="at-card">
            <h3 style={{ marginBottom: 'var(--at-space-2)' }}>Ações Operacionais</h3>
            <div className="at-actions">
              <Button type="button" variant="secondary" size="sm" onClick={() => onBaixarPdf(pedido)}>
                <FileDown size={14} aria-hidden="true" /> Baixar PDF
              </Button>
              <Button type="button" variant="secondary" size="sm" onClick={() => onAbrirPagamento(pedido)}>
                <CircleDollarSign size={14} aria-hidden="true" /> Pagamentos
              </Button>

              {pedido.status_geral === 'rascunho' && (
                <>
                  <Button type="button" variant="secondary" size="sm" onClick={() => onEditarRascunho(pedido)}>
                    <Edit3 size={14} aria-hidden="true" /> Editar Rascunho
                  </Button>
                  <Button
                    type="button"
                    variant="primary"
                    size="sm"
                    disabled={processando}
                    onClick={() => executarMudanca('geral', 'confirmado')}
                  >
                    <CheckCircle2 size={14} aria-hidden="true" /> Confirmar Pedido
                  </Button>
                </>
              )}

              {pedido.status_geral === 'confirmado' && preProducao && (
                <>
                  <Button type="button" variant="primary" size="sm" onClick={() => onAbrirBaixa(pedido)}>
                    <Hammer size={14} aria-hidden="true" /> Baixar e Produzir
                  </Button>
                  {pedido.status_producao !== 'aguardando_material' && (
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      disabled={processando}
                      onClick={() => executarMudanca('producao', 'aguardando_material')}
                    >
                      Aguardando Material
                    </Button>
                  )}
                  {pedido.status_producao !== 'na_fila' && (
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      disabled={processando}
                      onClick={() => executarMudanca('producao', 'na_fila')}
                    >
                      Enviar p/ Fila
                    </Button>
                  )}
                </>
              )}

              {pedido.status_geral === 'confirmado' && pedido.status_producao === 'em_producao' && (
                <Button
                  type="button"
                  variant="primary"
                  size="sm"
                  disabled={processando}
                  onClick={() => executarMudanca('producao', 'embalando')}
                >
                  Mover para Embalando
                </Button>
              )}

              {pedido.status_geral === 'confirmado' && pedido.status_producao === 'embalando' && (
                <Button
                  type="button"
                  variant="primary"
                  size="sm"
                  disabled={processando}
                  onClick={() => executarMudanca('producao', 'pronto_entrega')}
                >
                  Pronto para Entrega
                </Button>
              )}

              {pedido.status_geral === 'confirmado' && pedido.status_producao === 'pronto_entrega' && (
                <Button
                  type="button"
                  variant="primary"
                  size="sm"
                  disabled={processando}
                  onClick={() => executarMudanca('geral', 'entregue')}
                >
                  <PackageCheck size={14} aria-hidden="true" /> Marcar Entregue
                </Button>
              )}

              {pedido.status_geral === 'entregue' && (
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  disabled={processando}
                  onClick={() => executarMudanca('geral', 'arquivado')}
                >
                  <Archive size={14} aria-hidden="true" /> Arquivar
                </Button>
              )}

              {['rascunho', 'confirmado'].includes(pedido.status_geral) && (
                <Button
                  type="button"
                  variant="danger"
                  size="sm"
                  onClick={() => setConfirmCancelar(true)}
                >
                  <Ban size={14} aria-hidden="true" /> Cancelar Pedido
                </Button>
              )}

              {podeExcluir && (
                <Button
                  type="button"
                  variant="danger"
                  size="sm"
                  onClick={() => setConfirmExcluir(true)}
                >
                  <Trash2 size={14} aria-hidden="true" /> Excluir
                </Button>
              )}
            </div>
          </section>

          <section>
            <h3 style={{ marginBottom: 'var(--at-space-2)' }}>Itens e Especificações de Corte</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-2)' }}>
              {(pedido.itens || []).map((item) => (
                <div key={item.id} className="at-card">
                  <div className="at-pedido-card__top">
                    <strong>
                      {item.quantidade}× {item.descricao}
                    </strong>
                    <strong className="at-num">{formatarMoeda(item.subtotal)}</strong>
                  </div>
                  <div className="at-muted at-num" style={{ fontSize: 'var(--at-text-xs)' }}>
                    Unit. praticado: {formatarMoeda(item.preco_unitario)} (Sugerido: {formatarMoeda(item.valor_sugerido)})
                  </div>
                  {(item.molduras || []).length > 0 && (
                    <div className="at-muted at-num" style={{ fontSize: 'var(--at-text-xs)', marginTop: 4 }}>
                      {item.molduras.map((m, idx) => (
                        <div key={idx}>
                          Moldura {idx + 1} ({m.codigo_moldura_snapshot}): corte {m.largura_calculada_cm} ×{' '}
                          {m.altura_calculada_cm} cm · {formatarMetragem(m.metragem_total_m)} ({m.barras_sugeridas} bar.)
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          <section>
            <h3 style={{ marginBottom: 'var(--at-space-2)' }}>Histórico de Eventos</h3>
            <div className="at-timeline">
              {(pedido.eventos || []).map((ev) => (
                <div key={ev.id} className="at-timeline__item">
                  <strong>{ev.tipo_evento}</strong>
                  {ev.descricao && <div className="at-secondary">{ev.descricao}</div>}
                  <div className="at-muted" style={{ fontSize: 'var(--at-text-xs)' }}>
                    {formatarData(ev.criado_em)}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </Dialog>

      <ConfirmDialog
        open={confirmCancelar}
        onClose={() => setConfirmCancelar(false)}
        title={`Cancelar ${pedido.numero_pedido}?`}
        confirmLabel="Sim, Cancelar Pedido"
        loading={processando}
        onConfirm={async () => {
          await executarMudanca('geral', 'cancelado');
          setConfirmCancelar(false);
        }}
      >
        <p>Deseja realmente cancelar este pedido? Ele sairá da fila de produção.</p>
        {Number(pedido.valor_pago) > 0 && (
          <Callout variant="warning">
            Há {formatarMoeda(pedido.valor_pago)} já pagos neste pedido. Após cancelar, faça o estorno manual em Pagamentos.
          </Callout>
        )}
      </ConfirmDialog>

      <ConfirmDialog
        open={confirmExcluir}
        onClose={() => setConfirmExcluir(false)}
        title={`Excluir ${pedido.numero_pedido}?`}
        confirmLabel="Excluir Permanentemente"
        loading={processando}
        onConfirm={async () => {
          setProcessando(true);
          try {
            await onExcluirPedido(pedido);
            setConfirmExcluir(false);
          } finally {
            setProcessando(false);
          }
        }}
      >
        <p>Esta ação removerá o pedido permanentemente do banco de dados.</p>
      </ConfirmDialog>
    </>
  );
};

export default PedidoDetalhe;
