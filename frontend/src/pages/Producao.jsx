import React, { useState, useEffect, useCallback } from 'react';
import api from '../api/config';
import { Play, ChevronRight, Plus, RefreshCw, AlertTriangle, X, Clock } from 'lucide-react';
import ModalNovoPedido from '../components/ModalNovoPedido';
import ModalDetalhePedido from '../components/ModalDetalhePedido';

const STATUS_CORES = {
  pendente: '#f59e0b',
  aguardando_material: '#f97316',
  em_producao: '#8b5cf6',
  para_embalar: '#06b6d4',
  pronto_entrega: '#10b981',
  entregue: '#22c55e',
};

const STATUS_LABELS = {
  pendente: 'Pendente',
  aguardando_material: 'Aguardando Material',
  em_producao: 'Em Produção',
  para_embalar: 'Para Embalar',
  pronto_entrega: 'Pronto',
  entregue: 'Entregue',
};

const ORDEM_STATUS = ['pendente', 'aguardando_material', 'em_producao', 'para_embalar', 'pronto_entrega', 'entregue'];

const Producao = () => {
  const [pedidos, setPedidos] = useState([]);
  const [resumo, setResumo] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [selecionados, setSelecionados] = useState(new Set());
  const [processando, setProcessando] = useState(null);
  const [erro, setErro] = useState('');
  const [modalNovoPedido, setModalNovoPedido] = useState(false);
  const [pedidoDetalheId, setPedidoDetalheId] = useState(null);

  const carregarDados = useCallback(async () => {
    setCarregando(true);
    try {
      const [p, res] = await Promise.all([
        api.get('/pedidos/'),
        api.get('/producao/resumo'),
      ]);
      setPedidos(p.data);
      setResumo(res.data);
    } catch (err) {
      console.error('Erro ao carregar dados:', err);
    }
    setCarregando(false);
  }, []);

  useEffect(() => {
    carregarDados();
  }, [carregarDados]);

  const toggleSelecionado = (id) => {
    setSelecionados(prev => {
      const novos = new Set(prev);
      if (novos.has(id)) novos.delete(id);
      else novos.add(id);
      return novos;
    });
  };

  const iniciarSelecionados = async () => {
    if (selecionados.size === 0) return;
    setProcessando('iniciar');
    setErro('');
    try {
      const ids = Array.from(selecionados);
      const resp = await api.post('/producao/iniciar', { pedido_ids: ids });
      if (resp.data.total_erros > 0) {
        const msgs = resp.data.resultados.filter(r => !r.sucesso).map(r => `#${r.pedido_id}: ${r.mensagem}`);
        setErro(msgs.join('; '));
      }
      setSelecionados(new Set());
      await carregarDados();
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao iniciar produção');
    }
    setProcessando(null);
  };

  const avancarPedido = async (pedidoId) => {
    setProcessando(pedidoId);
    setErro('');
    try {
      await api.post(`/producao/${pedidoId}/avancar`);
      await carregarDados();
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao avançar pedido');
    }
    setProcessando(null);
  };

  const getBadge = (status, eixo) => {
    const cores = {
      geral: { rascunho: '#6b7280', confirmado: '#6366f1', cancelado: '#ef4444', entregue: '#22c55e', arquivado: '#9ca3af' },
      producao: STATUS_CORES,
      financeiro: { sem_pagamento: '#ef4444', sinal_recebido: '#f59e0b', pago_total: '#22c55e', estornado: '#dc2626' }
    };
    const labels = {
      geral: { rascunho: 'Rascunho', confirmado: 'Confirmado', cancelado: 'Cancelado', entregue: 'Entregue', arquivado: 'Arquivado' },
      financeiro: { sem_pagamento: 'Sem Pgto', sinal_recebido: 'Sinal', pago_total: 'Pago', estornado: 'Estornado' }
    };
    if (eixo === 'producao') return getStatusBadgeProducao(status);
    const cor = cores[eixo]?.[status] || '#6b7280';
    return (
      <span style={{ background: `${cor}20`, color: cor, padding: '2px 8px', borderRadius: '12px', fontSize: '0.7rem', fontWeight: 600 }}>
        {labels[eixo]?.[status] || status}
      </span>
    );
  };

  const getStatusBadgeProducao = (status) => {
    const cor = STATUS_CORES[status] || '#6b7280';
    return (
      <span style={{ background: `${cor}20`, color: cor, padding: '2px 8px', borderRadius: '12px', fontSize: '0.7rem', fontWeight: 600 }}>
        {STATUS_LABELS[status] || status}
      </span>
    );
  };

  const pedidosPorColuna = ORDEM_STATUS.reduce((acc, status) => {
    acc[status] = pedidos.filter(p => p.status_producao === status);
    return acc;
  }, {});

  const proximoStatus = (atual) => {
    const mapa = {
      pendente: 'em_producao',
      aguardando_material: 'em_producao',
      em_producao: 'para_embalar',
      para_embalar: 'pronto_entrega',
      pronto_entrega: 'entregue',
    };
    return mapa[atual] || atual;
  };

  if (carregando && pedidos.length === 0) {
    return (
      <div className="fade-in">
        <h1>Produção</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '2rem' }}>Carregando...</p>
      </div>
    );
  }

  return (
    <div className="producao-page fade-in">
      <header className="page-header">
        <div>
          <h1>Produção</h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            {resumo ? `${pedidos.length} pedidos no sistema` : ''}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {selecionados.size > 0 && (
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              {selecionados.size} selecionados
            </span>
          )}
          <button className="btn btn-primary btn-sm" onClick={() => setModalNovoPedido(true)}>
            <Plus size={16} /> Novo Pedido
          </button>
          <button
            className="btn btn-primary btn-sm"
            onClick={iniciarSelecionados}
            disabled={selecionados.size === 0 || processando === 'iniciar'}
          >
            <Play size={16} />
            {processando === 'iniciar' ? 'Iniciando...' : `Iniciar Produção (${selecionados.size})`}
          </button>
          <button className="btn btn-secondary btn-sm" onClick={carregarDados} title="Atualizar">
            <RefreshCw size={16} />
          </button>
        </div>
      </header>

      {erro && (
        <div style={{
          background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)',
          borderRadius: '8px', padding: '0.75rem 1rem', marginBottom: '1rem',
          display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', color: '#ef4444'
        }}>
          <AlertTriangle size={18} />
          {erro}
          <button style={{ marginLeft: 'auto', background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }} onClick={() => setErro('')}>
            <X size={16} />
          </button>
        </div>
      )}

      {resumo && (
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
          {ORDEM_STATUS.map(status => (
            <div key={status} style={{
              flex: '1', minWidth: '100px', background: 'rgba(255,255,255,0.02)',
              borderRadius: '8px', padding: '0.75rem', textAlign: 'center',
              border: `1px solid ${STATUS_CORES[status]}30`,
            }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: STATUS_CORES[status] }}>
                {resumo[status] || 0}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                {STATUS_LABELS[status]}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="kanban-board">
        {ORDEM_STATUS.map(status => (
          <div key={status} className="kanban-column">
            <div className="kanban-header" style={{ background: STATUS_CORES[status] }}>
              <span className="kanban-title">{STATUS_LABELS[status]}</span>
              <span className="kanban-count">{pedidosPorColuna[status]?.length || 0}</span>
            </div>
            <div className="kanban-body">
              {pedidosPorColuna[status]?.length > 0 ? (
                pedidosPorColuna[status].map(p => (
                  <div key={p.id} className="card producao-card" onClick={() => setPedidoDetalheId(p.id)}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                      {['pendente', 'aguardando_material'].includes(p.status_producao) && (
                        <input
                          type="checkbox"
                          checked={selecionados.has(p.id)}
                          onChange={(e) => { e.stopPropagation(); toggleSelecionado(p.id); }}
                          style={{ marginTop: '4px', accentColor: 'var(--accent-primary)' }}
                        />
                      )}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.25rem' }}>
                          <strong style={{ fontSize: '0.9rem' }}>#{p.numero_pedido}</strong>
                        </div>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                          {p.cliente?.nome || 'Cliente'} {p.cliente?.sobrenome || ''}
                        </p>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                          {p.itens?.length || 0} item(ns) — R$ {parseFloat(p.valor_total || 0).toFixed(2)}
                        </p>
                        <div style={{ display: 'flex', gap: '0.25rem', marginTop: '0.25rem', flexWrap: 'wrap' }}>
                          {getStatusBadgeProducao(p.status_producao)}
                          {getBadge(p.status_geral, 'geral')}
                          {getBadge(p.status_financeiro, 'financeiro')}
                        </div>
                      </div>
                    </div>
                    {status !== 'entregue' && (
                      <button
                        className="btn btn-secondary btn-sm"
                        style={{ width: '100%', marginTop: '0.5rem', fontSize: '0.75rem', padding: '0.4rem' }}
                        onClick={(e) => { e.stopPropagation(); avancarPedido(p.id); }}
                        disabled={processando === p.id}
                      >
                        {processando === p.id ? <Clock size={14} /> : <ChevronRight size={14} />}
                        {processando === p.id ? 'Avançando...' : `Avançar para ${STATUS_LABELS[proximoStatus(status)]}`}
                      </button>
                    )}
                  </div>
                ))
              ) : (
                <p className="kanban-empty" style={{ fontSize: '0.8rem' }}>Vazio</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {modalNovoPedido && (
        <ModalNovoPedido
          onFechar={() => setModalNovoPedido(false)}
          onCriado={carregarDados}
        />
      )}

      {pedidoDetalheId && (
        <ModalDetalhePedido
          pedidoId={pedidoDetalheId}
          onFechar={() => setPedidoDetalheId(null)}
          onAtualizar={carregarDados}
        />
      )}

      <style>{`
        .producao-card {
          padding: 0.75rem !important;
          margin-bottom: 0.5rem;
          cursor: pointer;
          transition: border-color 0.2s;
        }
        .producao-card:hover {
          border-color: var(--accent-primary);
        }
        .kanban-board {
          display: flex;
          gap: 0.75rem;
          overflow-x: auto;
          padding-bottom: 1rem;
          -webkit-overflow-scrolling: touch;
        }
        .kanban-column {
          min-width: 240px;
          flex: 0 0 240px;
          max-width: 300px;
        }
        .kanban-header {
          color: white;
          padding: 0.75rem 1rem;
          border-radius: 8px 8px 0 0;
          font-weight: 600;
          font-size: 0.85rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .kanban-count {
          background: rgba(255,255,255,0.25);
          padding: 0.15rem 0.6rem;
          border-radius: 20px;
          font-size: 0.8rem;
          font-weight: 600;
        }
        .kanban-body {
          background: var(--bg-secondary);
          padding: 0.75rem;
          border-radius: 0 0 8px 8px;
          min-height: 200px;
          max-height: calc(100vh - 320px);
          overflow-y: auto;
          border: 1px solid var(--glass-border);
          border-top: none;
        }
        .kanban-empty {
          color: var(--text-secondary);
          text-align: center;
          font-size: 0.9rem;
          padding: 1.5rem 0;
        }
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.7);
          display: flex;
          align-items: flex-start;
          justify-content: center;
          padding-top: 5vh;
          z-index: 1000;
        }
        .modal-content {
          background: var(--card-bg);
          padding: 2rem;
          border-radius: 12px;
          width: 90%;
          max-width: 500px;
          border: 1px solid var(--glass-border);
          max-height: 85vh;
          overflow-y: auto;
        }
        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 1.5rem;
        }
        .modal-header h2 {
          margin: 0;
        }
        @media (max-width: 767px) {
          .kanban-column {
            min-width: 200px;
            flex: 0 0 200px;
          }
          .kanban-body {
            max-height: 60vh;
          }
        }
      `}</style>
    </div>
  );
};

export default Producao;
