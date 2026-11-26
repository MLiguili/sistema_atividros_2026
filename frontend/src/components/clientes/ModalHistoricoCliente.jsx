import React, { useEffect, useState } from 'react';
import { ArrowLeft, ChevronRight, ExternalLink, FileDown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/config';
import { useToast } from '../../context/ContextoToast';
import Dialog from '../ui/Dialog';
import Button from '../ui/Button';
import StatusBadge from '../ui/StatusBadge';
import EmptyState from '../ui/EmptyState';
import Callout from '../ui/Callout';
import { formatarData, formatarMetragem, formatarMoeda } from '../../utils/formatadores';

/**
 * Modal de histórico de pedidos do cliente com drill-down completo ao clicar em qualquer pedido.
 *
 * @param {{
 *   cliente: { id: number, nome: string, sobrenome: string } | null,
 *   onClose: () => void
 * }} props Propriedades do modal.
 * @returns {JSX.Element | null} Modal de histórico e detalhes do pedido selecionado.
 */
const ModalHistoricoCliente = ({ cliente, onClose }) => {
  const navigate = useNavigate();
  const { notificar } = useToast();

  const [pedidos, setPedidos] = useState([]);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState('');
  const [pedidoSelecionado, setPedidoSelecionado] = useState(null);
  const [carregandoDetalhe, setCarregandoDetalhe] = useState(false);

  useEffect(() => {
    if (!cliente) return;
    let ativo = true;
    setCarregando(true);
    setErro('');
    setPedidoSelecionado(null);

    api
      .get(`/clientes/${cliente.id}/pedidos`)
      .then((resp) => {
        if (ativo) setPedidos(resp.data || []);
      })
      .catch((err) => {
        if (ativo) setErro(err.response?.data?.detail || 'Erro ao carregar histórico.');
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });

    return () => {
      ativo = false;
    };
  }, [cliente]);

  const abrirDetalhesPedido = async (pedidoResumo) => {
    setCarregandoDetalhe(true);
    setErro('');
    try {
      const resp = await api.get(`/pedidos/${pedidoResumo.id}`);
      setPedidoSelecionado(resp.data);
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao carregar informações do pedido.');
    } finally {
      setCarregandoDetalhe(false);
    }
  };

  const baixarPdf = async (pedido) => {
    try {
      const resp = await api.get(`/pedidos/${pedido.id}/pdf`, { responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }));
      const link = Object.assign(document.createElement('a'), {
        href: url,
        download: `${pedido.numero_pedido}.pdf`,
      });
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch {
      notificar('Erro ao baixar PDF do pedido.', 'danger');
    }
  };

  const titulo = pedidoSelecionado
    ? `Pedido #${pedidoSelecionado.numero_pedido}`
    : cliente
      ? `Histórico — ${cliente.nome} ${cliente.sobrenome}`
      : 'Histórico';

  return (
    <Dialog open={Boolean(cliente)} onClose={onClose} title={titulo} size="lg">
      {erro && <Callout variant="danger">{erro}</Callout>}

      {(carregando || carregandoDetalhe) && (
        <div className="at-state" role="status">
          {carregandoDetalhe ? 'Carregando detalhes do pedido...' : 'Carregando histórico de pedidos...'}
        </div>
      )}

      {!carregando && !carregandoDetalhe && !pedidoSelecionado && pedidos.length === 0 && !erro && (
        <EmptyState
          title="Nenhum pedido registrado"
          description="Este cliente ainda não possui orçamentos ou pedidos vinculados."
        />
      )}

      {!carregando && !carregandoDetalhe && !pedidoSelecionado && pedidos.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-3)' }}>
          {pedidos.map((p) => (
            <button
              key={p.id}
              type="button"
              className="at-pedido-card"
              onClick={() => abrirDetalhesPedido(p)}
              style={{ width: '100%', textAlign: 'left', cursor: 'pointer', color: 'inherit' }}
            >
              <div className="at-pedido-card__top">
                <div>
                  <strong className="at-num">#{p.numero_pedido}</strong>
                  <span className="at-muted" style={{ marginLeft: 'var(--at-space-2)' }}>
                    Criado em {formatarData(p.criado_em)}
                  </span>
                </div>
                <strong className="at-num">{formatarMoeda(p.valor_total)}</strong>
              </div>
              <div className="at-pedido-card__badges" style={{ marginTop: 'var(--at-space-2)' }}>
                <div className="at-actions">
                  <StatusBadge eixo="geral" status={p.status_geral} />
                  <StatusBadge eixo="producao" status={p.status_producao} />
                  <StatusBadge eixo="financeiro" status={p.status_financeiro} />
                </div>
                <span className="at-muted" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                  Ver detalhes <ChevronRight size={15} aria-hidden="true" />
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {!carregandoDetalhe && pedidoSelecionado && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-4)' }}>
          <div className="at-pedido-card__top">
            <Button type="button" variant="secondary" size="sm" onClick={() => setPedidoSelecionado(null)}>
              <ArrowLeft size={14} aria-hidden="true" /> Voltar ao histórico
            </Button>
            <div className="at-actions">
              <Button type="button" variant="secondary" size="sm" onClick={() => baixarPdf(pedidoSelecionado)}>
                <FileDown size={14} aria-hidden="true" /> Baixar PDF
              </Button>
              <Button
                type="button"
                variant="primary"
                size="sm"
                onClick={() => {
                  const idAbrir = pedidoSelecionado.id;
                  onClose();
                  navigate('/pedidos', { state: { abrirPedidoId: idAbrir } });
                }}
              >
                <ExternalLink size={14} aria-hidden="true" /> Abrir em Pedidos
              </Button>
            </div>
          </div>

          <div className="at-actions">
            <StatusBadge eixo="geral" status={pedidoSelecionado.status_geral} />
            <StatusBadge eixo="producao" status={pedidoSelecionado.status_producao} />
            <StatusBadge eixo="financeiro" status={pedidoSelecionado.status_financeiro} />
          </div>

          <div className="at-grid-3">
            <div className="at-card">
              <div className="at-muted">Datas</div>
              <div>Emissão: {formatarData(pedidoSelecionado.criado_em)}</div>
              <div>Validade: {formatarData(pedidoSelecionado.data_validade_orcamento)}</div>
              <div>Prazo: {formatarData(pedidoSelecionado.prazo_entrega)}</div>
            </div>
            <div className="at-card">
              <div className="at-muted">Entrega e Observações</div>
              <div>{pedidoSelecionado.endereco_entrega || 'Retirada / não informado'}</div>
              {pedidoSelecionado.observacoes && (
                <div className="at-muted" style={{ marginTop: 4 }}>{pedidoSelecionado.observacoes}</div>
              )}
            </div>
            <div className="at-card">
              <div className="at-muted">Resumo Financeiro</div>
              <div className="at-num">Subtotal: {formatarMoeda(pedidoSelecionado.subtotal_itens)}</div>
              <div className="at-num">Frete: {formatarMoeda(pedidoSelecionado.frete)}</div>
              <div className="at-num">
                Desconto: {pedidoSelecionado.desconto_tipo === 'percentual'
                  ? `${pedidoSelecionado.desconto_valor}%`
                  : formatarMoeda(pedidoSelecionado.desconto_valor)}
              </div>
              <strong className="at-num">Total: {formatarMoeda(pedidoSelecionado.valor_total)}</strong>
              <div className="at-num">Pago: {formatarMoeda(pedidoSelecionado.valor_pago)} · Devedor: {formatarMoeda(pedidoSelecionado.saldo_devedor)}</div>
            </div>
          </div>

          <section>
            <h3 style={{ marginBottom: 'var(--at-space-2)' }}>Itens do Pedido</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-2)' }}>
              {(pedidoSelecionado.itens || []).map((item) => (
                <div key={item.id} className="at-card">
                  <div className="at-pedido-card__top">
                    <strong>{item.quantidade}× {item.descricao}</strong>
                    <strong className="at-num">{formatarMoeda(item.subtotal)}</strong>
                  </div>
                  <div className="at-muted at-num" style={{ fontSize: 'var(--at-text-xs)' }}>
                    Unitário praticado: {formatarMoeda(item.preco_unitario)}
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
            <h3 style={{ marginBottom: 'var(--at-space-2)' }}>Pagamentos</h3>
            {(pedidoSelecionado.pagamentos || []).length === 0 ? (
              <p className="at-muted">Nenhum pagamento registrado.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-2)' }}>
                {pedidoSelecionado.pagamentos.map((pg) => (
                  <div key={pg.id} className="at-baixa-row">
                    <div>
                      <strong className="at-num">{formatarMoeda(pg.valor)}</strong>{' '}
                      <span className="at-muted">({pg.forma_pagamento})</span>
                      {pg.observacao && <div className="at-muted">{pg.observacao}</div>}
                    </div>
                    <span className="at-muted">
                      {formatarData(pg.data_pagamento)}{pg.estornado ? ' · ESTORNADO' : ''}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section>
            <h3 style={{ marginBottom: 'var(--at-space-2)' }}>Histórico de Eventos</h3>
            <div className="at-timeline">
              {(pedidoSelecionado.eventos || []).map((ev) => (
                <div key={ev.id} className="at-timeline__item">
                  <strong>
                    {ev.eixo}: {ev.status_anterior ? `${ev.status_anterior} → ` : ''}{ev.status_novo}
                  </strong>
                  {ev.observacao && <div className="at-secondary">{ev.observacao}</div>}
                  <div className="at-muted" style={{ fontSize: 'var(--at-text-xs)' }}>
                    {formatarData(ev.criado_em)}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </Dialog>
  );
};

export default ModalHistoricoCliente;
