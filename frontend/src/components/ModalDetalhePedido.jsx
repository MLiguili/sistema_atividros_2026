import React, { useState, useEffect } from 'react';
import api from '../api/config';
import { X, FileText, History, AlertTriangle, CheckCircle } from 'lucide-react';

const STATUS_CORES = {
  geral: { rascunho: '#6b7280', confirmado: '#6366f1', cancelado: '#ef4444', entregue: '#22c55e', arquivado: '#9ca3af' },
  producao: { pendente: '#f59e0b', aguardando_material: '#f97316', em_producao: '#8b5cf6', para_embalar: '#06b6d4', pronto_entrega: '#10b981', entregue: '#22c55e' },
  financeiro: { sem_pagamento: '#ef4444', sinal_recebido: '#f59e0b', pago_total: '#22c55e', estornado: '#dc2626' }
};

const STATUS_LABELS = {
  geral: { rascunho: 'Rascunho', confirmado: 'Confirmado', cancelado: 'Cancelado', entregue: 'Entregue', arquivado: 'Arquivado' },
  producao: { pendente: 'Pendente', aguardando_material: 'Aguardando Material', em_producao: 'Em Produção', para_embalar: 'Para Embalar', pronto_entrega: 'Pronto', entregue: 'Entregue' },
  financeiro: { sem_pagamento: 'Sem Pgto', sinal_recebido: 'Sinal', pago_total: 'Pago', estornado: 'Estornado' }
};

const StatusBadge = ({ status, eixo }) => {
  const cor = STATUS_CORES[eixo]?.[status] || '#6b7280';
  const label = STATUS_LABELS[eixo]?.[status] || status;
  return (
    <span style={{ background: cor, color: 'white', padding: '2px 8px', borderRadius: '12px', fontSize: '0.7rem', fontWeight: 500 }}>
      {label}
    </span>
  );
};

const ModalDetalhePedido = ({ pedidoId, onFechar, onAtualizar }) => {
  const [pedido, setPedido] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [modalSinal, setModalSinal] = useState(null);
  const [confirmandoBaixa, setConfirmandoBaixa] = useState(false);
  const [valorSinal, setValorSinal] = useState('');

  const carregarPedido = async () => {
    try {
      const resp = await api.get(`/pedidos/${pedidoId}`);
      setPedido(resp.data);
    } catch { console.error('Erro ao carregar pedido'); }
    setCarregando(false);
  };

  useEffect(() => { carregarPedido(); }, [pedidoId]);

  const atualizarStatus = async (eixo, novoStatus, sinal = null) => {
    try {
      const payload = { eixo, novo_status: novoStatus };
      if (sinal !== null) payload.valor_sinal = sinal;
      await api.patch(`/pedidos/${pedidoId}/status`, payload);
      await carregarPedido();
      onAtualizar();
    } catch (erro) {
      alert('Erro: ' + (erro.response?.data?.detail || erro.message));
    }
  };

  const confirmarBaixaEstoque = async () => {
    try {
      await api.post(`/pedidos/${pedidoId}/baixa-estoque`);
      setConfirmandoBaixa(false);
      await carregarPedido();
      onAtualizar();
    } catch (erro) {
      alert('Erro: ' + (erro.response?.data?.detail || erro.message));
    }
  };

  const baixarPDF = async () => {
    try {
      const resposta = await api.get(`/pedidos/${pedidoId}/pdf`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([resposta.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `pedido_${pedidoId}.pdf`);
      document.body.appendChild(link);
      link.click();
    } catch { console.error('Erro ao baixar PDF'); }
  };

  if (carregando) {
    return (
      <div className="modal-overlay" onClick={onFechar}>
        <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '700px', textAlign: 'center', padding: '3rem' }}>
          <p>Carregando...</p>
        </div>
      </div>
    );
  }

  if (!pedido) {
    return (
      <div className="modal-overlay" onClick={onFechar}>
        <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '400px', textAlign: 'center', padding: '2rem' }}>
          <p>Pedido não encontrado.</p>
          <button className="btn btn-primary" onClick={onFechar} style={{ marginTop: '1rem' }}>Fechar</button>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="modal-overlay" onClick={onFechar}>
        <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '800px', maxHeight: '90vh', overflowY: 'auto' }}>
          <div className="modal-header">
            <div>
              <h2>Pedido #{pedido.numero_pedido}</h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                {pedido.cliente?.nome} {pedido.cliente?.sobrenome}
              </p>
            </div>
            <button className="btn-icon" onClick={onFechar}><X size={20} /></button>
          </div>

          <div className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
            <h3 style={{ marginBottom: '0.75rem' }}>Status</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{ width: '90px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Geral:</span>
                <StatusBadge status={pedido.status_geral} eixo="geral" />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{ width: '90px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Produção:</span>
                <StatusBadge status={pedido.status_producao} eixo="producao" />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{ width: '90px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Financeiro:</span>
                <StatusBadge status={pedido.status_financeiro} eixo="financeiro" />
              </div>
            </div>
          </div>

          <div className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
            <h3 style={{ marginBottom: '0.75rem' }}>Itens</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--glass-border)' }}>
                  <th style={{ textAlign: 'left', padding: '0.4rem', color: 'var(--text-secondary)' }}>Descrição</th>
                  <th style={{ textAlign: 'center', padding: '0.4rem', color: 'var(--text-secondary)' }}>Qtd</th>
                  <th style={{ textAlign: 'right', padding: '0.4rem', color: 'var(--text-secondary)' }}>Unitário</th>
                  <th style={{ textAlign: 'right', padding: '0.4rem', color: 'var(--text-secondary)' }}>Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {pedido.itens?.map(item => (
                  <tr key={item.id} style={{ borderBottom: '1px solid var(--glass-border)' }}>
                    <td style={{ padding: '0.5rem' }}>{item.descricao}</td>
                    <td style={{ padding: '0.5rem', textAlign: 'center' }}>{item.quantidade}</td>
                    <td style={{ padding: '0.5rem', textAlign: 'right' }}>R$ {parseFloat(item.preco_unitario).toFixed(2)}</td>
                    <td style={{ padding: '0.5rem', textAlign: 'right' }}>R$ {parseFloat(item.subtotal).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div className="card" style={{ padding: '1rem' }}>
              <h3 style={{ marginBottom: '0.75rem' }}>Valores</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Total:</span>
                  <span>R$ {parseFloat(pedido.valor_total).toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Sinal:</span>
                  <span>R$ {parseFloat(pedido.valor_sinal).toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold' }}>
                  <span>Saldo:</span>
                  <span style={{ color: pedido.saldo_devedor > 0 ? 'var(--danger)' : 'var(--accent-primary)' }}>
                    R$ {parseFloat(pedido.saldo_devedor).toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            <div className="card" style={{ padding: '1rem' }}>
              <h3 style={{ marginBottom: '0.75rem' }}>Ações</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {pedido.status_geral === 'rascunho' && (
                  <button className="btn btn-primary btn-sm" onClick={() => atualizarStatus('geral', 'confirmado')}>
                    Confirmar Pedido
                  </button>
                )}
                {pedido.status_geral === 'confirmado' && (
                  <button className="btn btn-primary btn-sm" onClick={() => atualizarStatus('geral', 'entregue')}>
                    Marcar Entregue
                  </button>
                )}
                {['pendente', 'aguardando_material'].includes(pedido.status_producao) && (
                  <button className="btn btn-primary btn-sm" onClick={() => setConfirmandoBaixa(true)}>
                    Dar Baixa no Estoque
                  </button>
                )}
                {['rascunho', 'confirmado'].includes(pedido.status_geral) && (
                  <button className="btn btn-sm" style={{ background: 'var(--danger)', color: 'white' }}
                    onClick={() => {
                      if (pedido.status_financeiro === 'sinal_recebido' && !confirm('Este pedido tem sinal. O cancelamento estornará automaticamente. Continuar?')) return;
                      atualizarStatus('geral', 'cancelado');
                    }}>
                    Cancelar
                  </button>
                )}
                {pedido.status_financeiro === 'sem_pagamento' && (
                  <button className="btn btn-secondary btn-sm" onClick={() => setModalSinal(true)}>
                    Receber Sinal
                  </button>
                )}
                {pedido.status_financeiro === 'sinal_recebido' && (
                  <button className="btn btn-secondary btn-sm" onClick={() => atualizarStatus('financeiro', 'pago_total')}>
                    Quitar
                  </button>
                )}
                <button className="btn btn-secondary btn-sm" onClick={baixarPDF}>
                  <FileText size={16} /> Baixar PDF
                </button>
              </div>
            </div>
          </div>

          <div className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
            <h3 style={{ marginBottom: '0.75rem' }}>Status de Produção</h3>
            <select className="input-control" value={pedido.status_producao}
              onChange={(e) => atualizarStatus('producao', e.target.value)} style={{ width: '100%' }}>
              <option value="pendente">Pendente</option>
              <option value="aguardando_material">Aguardando Material</option>
              <option value="em_producao">Em Produção</option>
              <option value="para_embalar">Para Embalar</option>
              <option value="pronto_entrega">Pronto para Entrega</option>
              <option value="entregue">Entregue</option>
            </select>
          </div>

          <div className="card" style={{ padding: '1rem' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <History size={18} /> Histórico
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '250px', overflowY: 'auto' }}>
              {pedido.eventos?.length > 0 ? (
                pedido.eventos.map(evento => (
                  <div key={evento.id} style={{ fontSize: '0.85rem', padding: '0.5rem', background: 'rgba(255,255,255,0.02)', borderRadius: '6px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span style={{ fontWeight: 500 }}>[{evento.eixo}]</span>
                      <span style={{ color: 'var(--text-secondary)' }}>
                        {new Date(evento.criado_em).toLocaleDateString('pt-BR')}
                      </span>
                    </div>
                    <div style={{ color: 'var(--text-secondary)' }}>
                      {evento.status_anterior || '—'} → {evento.status_novo}
                    </div>
                    {evento.observacao && (
                      <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic', marginTop: '0.25rem', fontSize: '0.8rem' }}>
                        {evento.observacao}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <p style={{ color: 'var(--text-secondary)', textAlign: 'center' }}>Nenhum evento registrado</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {modalSinal && (
        <div className="modal-overlay" onClick={() => setModalSinal(false)} style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1100 }}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '400px' }}>
            <div className="modal-header">
              <h2>Receber Sinal</h2>
              <button className="btn-icon" onClick={() => setModalSinal(false)}><X size={20} /></button>
            </div>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.9rem' }}>
              Informe o valor do sinal. Não pode exceder R$ {parseFloat(pedido.valor_total).toFixed(2)}.
            </p>
            <div className="form-group">
              <label>Valor do Sinal (R$)</label>
              <input type="number" className="input-control" value={valorSinal}
                onChange={(e) => setValorSinal(e.target.value)} placeholder="0.00" step="0.01" autoFocus />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <span>Total do pedido:</span>
              <span>R$ {parseFloat(pedido.valor_total).toFixed(2)}</span>
            </div>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
              <button className="btn btn-secondary" onClick={() => setModalSinal(false)}>Cancelar</button>
              <button className="btn btn-primary" onClick={() => {
                const valor = parseFloat(valorSinal);
                if (isNaN(valor) || valor <= 0) return alert('Informe um valor válido maior que zero.');
                if (valor > parseFloat(pedido.valor_total)) return alert('O valor não pode exceder o total do pedido.');
                atualizarStatus('financeiro', 'sinal_recebido', valor);
                setModalSinal(false);
                setValorSinal('');
              }}>Confirmar</button>
            </div>
          </div>
        </div>
      )}

      {confirmandoBaixa && (
        <div className="modal-overlay" onClick={() => setConfirmandoBaixa(false)} style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1100 }}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '450px' }}>
            <div className="modal-header">
              <h2>Confirmar Baixa de Estoque</h2>
              <button className="btn-icon" onClick={() => setConfirmandoBaixa(false)}><X size={20} /></button>
            </div>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>Será dada baixa no estoque dos itens:</p>
            {pedido.itens?.map((item, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: '0.3rem', padding: '0.25rem 0.5rem', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                <span>{item.descricao}</span>
                <span style={{ color: 'var(--accent-primary)' }}>x{item.quantidade}</span>
              </div>
            ))}
            <p style={{ color: 'var(--warning)', fontSize: '0.85rem', marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertTriangle size={16} /> Essa ação não pode ser desfeita.
            </p>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
              <button className="btn btn-secondary" onClick={() => setConfirmandoBaixa(false)}>Cancelar</button>
              <button className="btn btn-primary" onClick={confirmarBaixaEstoque}>Confirmar Baixa</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ModalDetalhePedido;
