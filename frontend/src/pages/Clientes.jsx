import React, { useState, useEffect } from 'react';
import api from '../api/config';
import { Plus, Search, User, Phone, Mail, MapPin, Edit2, Trash2, X, Save, AlertTriangle, History, ShoppingCart } from 'lucide-react';

const Clientes = () => {
  const [clientes, setClientes] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [termoBusca, setTermoBusca] = useState('');
  const [modalAberto, setModalAberto] = useState(null);
  const [clienteEditando, setClienteEditando] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [erro, setErro] = useState('');
  const [historicoCliente, setHistoricoCliente] = useState(null);
  const [pedidosCliente, setPedidosCliente] = useState([]);

  const carregarClientes = async () => {
    setCarregando(true);
    try {
      const resposta = await api.get('/clientes/');
      setClientes(resposta.data);
    } catch (erro) {
      console.error('Erro ao carregar clientes:', erro);
    }
    setCarregando(false);
  };

  useEffect(() => {
    carregarClientes();
  }, []);

  const filtrados = clientes.filter(c => 
    `${c.nome} ${c.sobrenome}`.toLowerCase().includes(termoBusca.toLowerCase()) ||
    (c.email && c.email.toLowerCase().includes(termoBusca.toLowerCase())) ||
    (c.telefone && c.telefone.includes(termoBusca))
  );

  const abrirModalCriar = () => {
    setClienteEditando(null);
    setErro('');
    setModalAberto('criar');
  };

  const abrirModalEditar = (cliente) => {
    setClienteEditando(cliente);
    setErro('');
    setModalAberto('editar');
  };

  const fecharModal = () => {
    setModalAberto(null);
    setClienteEditando(null);
    setErro('');
  };

  const handleSalvar = async (dados) => {
    try {
      if (clienteEditando) {
        await api.put(`/clientes/${clienteEditando.id}`, dados);
      } else {
        await api.post('/clientes/', dados);
      }
      carregarClientes();
      fecharModal();
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao salvar');
    }
  };

  const handleDeletar = async (id) => {
    try {
      await api.delete(`/clientes/${id}`);
      carregarClientes();
      setConfirmDelete(null);
    } catch (err) {
      alert('Erro ao deletar: ' + (err.response?.data?.detail || err.message));
    }
  };

  const abrirHistorico = async (cliente) => {
    setHistoricoCliente(cliente);
    try {
      const resposta = await api.get('/pedidos/');
      const pedidosDoCliente = resposta.data.filter(p => p.cliente_id === cliente.id);
      setPedidosCliente(pedidosDoCliente.sort((a, b) => new Date(b.criado_em) - new Date(a.criado_em)));
    } catch (err) {
      console.error('Erro ao carregar pedidos:', err);
      setPedidosCliente([]);
    }
  };

  return (
    <div className="clientes-page fade-in">
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>Gestão de Clientes</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Visualize e gerencie sua base de contatos.</p>
        </div>
        <button className="btn btn-primary" onClick={abrirModalCriar}>
          <Plus size={20} /> Adicionar Cliente
        </button>
      </header>

      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem', display: 'flex', gap: '1rem' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
          <input 
            type="text" 
            placeholder="Buscar por nome ou email..." 
            className="input-control" 
            style={{ paddingLeft: '40px' }}
            value={termoBusca}
            onChange={(e) => setTermoBusca(e.target.value)}
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
        {carregando ? (
          <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '3rem' }}>Carregando clientes...</div>
        ) : filtrados.length > 0 ? (
          filtrados.map(c => (
            <div key={c.id} className="card fade-in" style={{ padding: '1.25rem', position: 'relative' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: 'rgba(99, 102, 241, 0.1)', color: '#6366f1', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <User size={20} />
                </div>
                <div style={{ display: 'flex', gap: '0.25rem' }}>
                  <button className="btn-icon" onClick={() => abrirModalEditar(c)} title="Editar">
                    <Edit2 size={16} />
                  </button>
                  <button className="btn-icon" onClick={() => setConfirmDelete(c)} title="Excluir">
                    <Trash2 size={16} color="var(--danger)" />
                  </button>
                </div>
              </div>
              
              <h3 style={{ marginBottom: '1rem' }}>{c.nome} {c.sobrenome}</h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Phone size={14} /> {c.telefone || 'Sem telefone'}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Mail size={14} /> {c.email || 'Sem email'}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <MapPin size={14} /> {c.endereco ? (c.endereco.length > 30 ? c.endereco.substring(0, 30) + '...' : c.endereco) : 'Sem endereço'}
                </div>
              </div>

              <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Cliente desde: {new Date(c.criado_em).toLocaleDateString('pt-BR')}</span>
                <button className="btn btn-glass" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }} onClick={() => abrirHistorico(c)}>
                  <History size={14} /> Historico
                </button>
              </div>
            </div>
          ))
        ) : (
          <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>Nenhum cliente encontrado.</div>
        )}
      </div>

      <style>{`
        .btn-icon { background: none; border: none; cursor: pointer; color: var(--text-secondary); transition: color 0.2s; }
        .btn-icon:hover { color: var(--text-primary); }
        .text-danger { color: var(--danger); }
        .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000; }
        .modal-content { background: var(--card-bg); border: 1px solid var(--glass-border); border-radius: 12px; padding: 2rem; width: 100%; max-width: 500px; max-height: 90vh; overflow-y: auto; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
        .modal-footer { display: flex; gap: 1rem; justify-content: flex-end; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--glass-border); }
        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .form-group { margin-bottom: 1rem; }
        label { display: block; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.5rem; }
      `}</style>

      {modalAberto && (
        <ModalCliente
          cliente={clienteEditando}
          onSalvar={handleSalvar}
          onFechar={fecharModal}
          erro={erro}
        />
      )}

      {confirmDelete && (
        <ModalConfirmacao
          cliente={confirmDelete}
          onConfirmar={() => handleDeletar(confirmDelete.id)}
          onCancelar={() => setConfirmDelete(null)}
        />
      )}

      {historicoCliente && (
        <ModalHistorico
          cliente={historicoCliente}
          pedidos={pedidosCliente}
          onFechar={() => { setHistoricoCliente(null); setPedidosCliente([]); }}
        />
      )}
    </div>
  );
};

function ModalCliente({ cliente, onSalvar, onFechar, erro }) {
  const [dados, setDados] = useState(cliente ? { ...cliente } : { nome: '', sobrenome: '', telefone: '', email: '', endereco: '', cep: '' });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSalvar(dados);
  };

  const setCampo = (campo, valor) => setDados({ ...dados, [campo]: valor });

  return (
    <div className="modal-overlay" onClick={onFechar}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{cliente ? 'Editar Cliente' : 'Novo Cliente'}</h2>
          <button className="btn-icon" onClick={onFechar}><X size={20} /></button>
        </div>

        {erro && (
          <div style={{ background: 'rgba(239,68,68,0.1)', color: 'var(--danger)', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertTriangle size={16} /> {erro}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="form-group">
              <label>Nome *</label>
              <input type="text" className="input-control" value={dados.nome} onChange={e => setCampo('nome', e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Sobrenome *</label>
              <input type="text" className="input-control" value={dados.sobrenome} onChange={e => setCampo('sobrenome', e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Telefone *</label>
              <input type="text" className="input-control" value={dados.telefone} onChange={e => setCampo('telefone', e.target.value)} placeholder="(00) 00000-0000" required />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input type="email" className="input-control" value={dados.email || ''} onChange={e => setCampo('email', e.target.value)} />
            </div>
            <div className="form-group" style={{ gridColumn: 'span 2' }}>
              <label>Endereço</label>
              <input type="text" className="input-control" value={dados.endereco || ''} onChange={e => setCampo('endereco', e.target.value)} />
            </div>
            <div className="form-group">
              <label>CEP</label>
              <input type="text" className="input-control" value={dados.cep || ''} onChange={e => setCampo('cep', e.target.value)} placeholder="00000-000" />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-glass" onClick={onFechar}>Cancelar</button>
            <button type="submit" className="btn btn-primary"><Save size={18} /> Salvar</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ModalConfirmacao({ cliente, onConfirmar, onCancelar }) {
  return (
    <div className="modal-overlay" onClick={onCancelar}>
      <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '400px' }}>
        <div style={{ textAlign: 'center' }}>
          <AlertTriangle size={48} color="var(--danger)" style={{ marginBottom: '1rem' }} />
          <h3 style={{ marginBottom: '1rem' }}>Confirmar Exclusão</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
            Tem certeza que deseja excluir <strong>{cliente.nome} {cliente.sobrenome}</strong>? Esta ação não pode ser desfeita.
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button className="btn btn-glass" onClick={onCancelar}>Cancelar</button>
            <button className="btn" style={{ background: 'var(--danger)', color: 'white' }} onClick={onConfirmar}>
              <Trash2 size={18} /> Excluir
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ModalHistorico({ cliente, pedidos, onFechar }) {
  const getStatusBadge = (status, eixo) => {
    const cores = {
      geral: { rascunho: '#6b7280', confirmado: '#6366f1', cancelado: '#ef4444', entregue: '#22c55e', arquivado: '#9ca3af' },
      producao: { pendente: '#f59e0b', aguardando_material: '#f97316', em_producao: '#8b5cf6', para_embalar: '#06b6d4', pronto_entrega: '#10b981', entregue: '#22c55e' },
      financeiro: { sem_pagamento: '#ef4444', sinal_recebido: '#f59e0b', pago_total: '#22c55e', estornado: '#dc2626' }
    };
    const labels = {
      geral: { rascunho: 'Rascunho', confirmado: 'Confirmado', cancelado: 'Cancelado', entregue: 'Entregue', arquivado: 'Arquivado' },
      producao: { pendente: 'Pendente', aguardando_material: 'Aguard.', em_producao: 'Producao', para_embalar: 'Embalar', pronto_entrega: 'Pronto', entregue: 'Entregue' },
      financeiro: { sem_pagamento: 'Sem Pgto', sinal_recebido: 'Sinal', pago_total: 'Pago', estornado: 'Estornado' }
    };
    return (
      <span style={{ 
        background: cores[eixo]?.[status] || '#6b7280', 
        color: 'white', 
        padding: '2px 6px', 
        borderRadius: '10px', 
        fontSize: '0.65rem',
        fontWeight: 500
      }}>
        {labels[eixo]?.[status] || status}
      </span>
    );
  };

  const totalGasto = pedidos.reduce((acc, p) => acc + parseFloat(p.valor_total || 0), 0);

  return (
    <div className="modal-overlay" onClick={onFechar}>
      <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '600px' }}>
        <div className="modal-header">
          <h2>Historico de {cliente.nome} {cliente.sobrenome}</h2>
          <button className="btn-icon" onClick={onFechar}><X size={20} /></button>
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ flex: 1, background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', textAlign: 'center' }}>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Pedidos</p>
            <p style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{pedidos.length}</p>
          </div>
          <div style={{ flex: 1, background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', textAlign: 'center' }}>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Total Gasto</p>
            <p style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>R$ {totalGasto.toFixed(2)}</p>
          </div>
        </div>

        {pedidos.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '400px', overflowY: 'auto' }}>
            {pedidos.map(pedido => (
              <div key={pedido.id} style={{ 
                padding: '0.75rem', 
                background: 'rgba(255,255,255,0.02)', 
                borderRadius: '8px',
                border: '1px solid var(--glass-border)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                  <div>
                    <p style={{ fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <ShoppingCart size={14} /> #{pedido.numero_pedido}
                    </p>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      {new Date(pedido.criado_em).toLocaleDateString('pt-BR')}
                    </p>
                  </div>
                  <span style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>
                    R$ {parseFloat(pedido.valor_total || 0).toFixed(2)}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '0.25rem' }}>
                  {getStatusBadge(pedido.status_geral, 'geral')}
                  {getStatusBadge(pedido.status_producao, 'producao')}
                  {getStatusBadge(pedido.status_financeiro, 'financeiro')}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>
            Nenhum pedido encontrado para este cliente.
          </div>
        )}

        <div className="modal-footer">
          <button className="btn btn-glass" onClick={onFechar}>Fechar</button>
        </div>
      </div>
    </div>
  );
}

export default Clientes;
