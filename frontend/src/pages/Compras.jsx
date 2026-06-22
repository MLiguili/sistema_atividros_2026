import React, { useState, useEffect, useCallback } from 'react';
import api from '../api/config';
import { Plus, X, Save, Package, Truck, Lightbulb, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

const STATUS_CORES = {
  pendente: '#f59e0b',
  enviada: '#3b82f6',
  parcial: '#8b5cf6',
  recebida: '#22c55e',
  cancelada: '#ef4444',
};

const TIPO_PRODUTO_LABEL = {
  moldura: 'Moldura',
  vidro: 'Vidro',
  fundo: 'Fundo',
  suplemento: 'Suplemento',
};

const Compras = () => {
  const [aba, setAba] = useState('fornecedores');
  const [fornecedores, setFornecedores] = useState([]);
  const [ordens, setOrdens] = useState([]);
  const [sugestoes, setSugestoes] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [showOrdemForm, setShowOrdemForm] = useState(false);
  const [erro, setErro] = useState('');

  const carregarFornecedores = useCallback(async () => {
    try {
      const resp = await api.get('/compras/fornecedores');
      setFornecedores(resp.data);
    } catch (err) {
      console.error(err);
    }
  }, []);

  const carregarOrdens = useCallback(async () => {
    try {
      const resp = await api.get('/compras/ordens');
      setOrdens(resp.data);
    } catch (err) {
      console.error(err);
    }
  }, []);

  const carregarSugestoes = useCallback(async () => {
    try {
      const resp = await api.get('/compras/sugerir');
      setSugestoes(resp.data);
    } catch (err) {
      console.error(err);
    }
  }, []);

  useEffect(() => {
    if (aba === 'fornecedores') carregarFornecedores();
    if (aba === 'ordens') carregarOrdens();
    if (aba === 'sugestoes') carregarSugestoes();
  }, [aba, carregarFornecedores, carregarOrdens, carregarSugestoes]);

  return (
    <div className="compras-page fade-in">
      <header className="page-header">
        <h1>Compras</h1>
      </header>

      <div className="tabs">
        <button className={`tab ${aba === 'fornecedores' ? 'active' : ''}`} onClick={() => setAba('fornecedores')}>
          <Truck size={16} /> Fornecedores
        </button>
        <button className={`tab ${aba === 'ordens' ? 'active' : ''}`} onClick={() => setAba('ordens')}>
          <Package size={16} /> Ordens de Compra
        </button>
        <button className={`tab ${aba === 'sugestoes' ? 'active' : ''}`} onClick={() => setAba('sugestoes')}>
          <Lightbulb size={16} /> Sugestões
        </button>
      </div>

      {aba === 'fornecedores' && (
        <FornecedoresTab
          fornecedores={fornecedores}
          onRefresh={carregarFornecedores}
        />
      )}

      {aba === 'ordens' && (
        <OrdensTab
          ordens={ordens}
          onRefresh={carregarOrdens}
          fornecedores={fornecedores}
          onCarregarFornecedores={carregarFornecedores}
          erro={erro}
          setErro={setErro}
        />
      )}

      {aba === 'sugestoes' && (
        <SugestoesTab
          sugestoes={sugestoes}
          onRefresh={carregarSugestoes}
          onOrdemCriada={() => { setAba('ordens'); carregarOrdens(); }}
        />
      )}
    </div>
  );
};

const FornecedoresTab = ({ fornecedores, onRefresh }) => {
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState(null);
  const [form, setForm] = useState({ nome: '', contato: '', telefone: '', email: '', endereco: '', cep: '' });

  const salvar = async () => {
    if (!form.nome || !form.telefone) return alert('Nome e telefone sao obrigatorios');
    try {
      if (editando) {
        await api.put(`/compras/fornecedores/${editando.id}`, form);
      } else {
        await api.post('/compras/fornecedores', form);
      }
      setShowForm(false);
      setEditando(null);
      setForm({ nome: '', contato: '', telefone: '', email: '', endereco: '', cep: '' });
      onRefresh();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao salvar');
    }
  };

  const editar = (f) => {
    setEditando(f);
    setForm({ nome: f.nome, contato: f.contato || '', telefone: f.telefone, email: f.email || '', endereco: f.endereco || '', cep: f.cep || '' });
    setShowForm(true);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <button className="btn btn-primary btn-sm" onClick={() => { setEditando(null); setForm({ nome: '', contato: '', telefone: '', email: '', endereco: '', cep: '' }); setShowForm(true); }}>
          <Plus size={16} /> Novo Fornecedor
        </button>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group"><label>Nome *</label><input className="input-control" value={form.nome} onChange={e => setForm({ ...form, nome: e.target.value })} /></div>
            <div className="form-group"><label>Contato</label><input className="input-control" value={form.contato} onChange={e => setForm({ ...form, contato: e.target.value })} /></div>
            <div className="form-group"><label>Telefone *</label><input className="input-control" value={form.telefone} onChange={e => setForm({ ...form, telefone: e.target.value })} /></div>
            <div className="form-group"><label>Email</label><input className="input-control" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></div>
            <div className="form-group"><label>Endereço</label><input className="input-control" value={form.endereco} onChange={e => setForm({ ...form, endereco: e.target.value })} /></div>
            <div className="form-group"><label>CEP</label><input className="input-control" value={form.cep} onChange={e => setForm({ ...form, cep: e.target.value })} /></div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
            <button className="btn btn-secondary btn-sm" onClick={() => setShowForm(false)}>Cancelar</button>
            <button className="btn btn-primary btn-sm" onClick={salvar}><Save size={16} /> Salvar</button>
          </div>
        </div>
      )}

      <div className="grid-auto">
        {fornecedores.map(f => (
          <div key={f.id} className="card" style={{ cursor: 'pointer' }} onClick={() => editar(f)}>
            <h3>{f.nome}</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{f.telefone}</p>
            {f.email && <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{f.email}</p>}
            {f.contato && <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Contato: {f.contato}</p>}
          </div>
        ))}
      </div>
    </div>
  );
};

const OrdensTab = ({ ordens, onRefresh, fornecedores, onCarregarFornecedores, erro, setErro }) => {
  const [showForm, setShowForm] = useState(false);
  const [showReceber, setShowReceber] = useState(null);
  const [receberQtds, setReceberQtds] = useState({});
  const [itens, setItens] = useState([{ produto_tipo: 'moldura', produto_id: '', quantidade_solicitada: 1, preco_unitario: '' }]);
  const [form, setForm] = useState({ fornecedor_id: '', observacao: '' });
  const [produtos, setProdutos] = useState({ molduras: [], vidros: [], fundos: [], suplementos: [] });

  useEffect(() => {
    const carregarProdutos = async () => {
      try {
        const [m, v, f, s] = await Promise.all([
          api.get('/estoque/molduras'),
          api.get('/estoque/vidros'),
          api.get('/estoque/fundos'),
          api.get('/estoque/suplementos'),
        ]);
        setProdutos({ molduras: m.data, vidros: v.data, fundos: f.data, suplementos: s.data });
      } catch (err) { console.error(err); }
    };
    if (showForm) { carregarProdutos(); onCarregarFornecedores(); }
  }, [showForm, onCarregarFornecedores]);

  const criarOrdem = async () => {
    if (!form.fornecedor_id) return alert('Selecione um fornecedor');
    try {
      await api.post('/compras/ordens', {
        fornecedor_id: parseInt(form.fornecedor_id),
        itens: itens.filter(i => i.produto_id).map(i => ({
          produto_tipo: i.produto_tipo,
          produto_id: parseInt(i.produto_id),
          quantidade_solicitada: parseInt(i.quantidade_solicitada),
          preco_unitario: parseFloat(i.preco_unitario),
        })),
        observacao: form.observacao || null,
      });
      setShowForm(false);
      setItens([{ produto_tipo: 'moldura', produto_id: '', quantidade_solicitada: 1, preco_unitario: '' }]);
      setForm({ fornecedor_id: '', observacao: '' });
      onRefresh();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao criar ordem');
    }
  };

  const receberOrdem = async (ordemId) => {
    const receberItens = Object.entries(receberQtds)
      .filter(([_, qtd]) => qtd && parseInt(qtd) > 0)
      .map(([itemId, qtd]) => ({ item_id: parseInt(itemId), quantidade_recebida: parseInt(qtd) }));

    if (receberItens.length === 0) return alert('Informe ao menos um item para receber');

    try {
      await api.post(`/compras/ordens/${ordemId}/receber`, { itens: receberItens });
      setShowReceber(null);
      setReceberQtds({});
      onRefresh();
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao receber');
    }
  };

  const produtosDisponiveis = (tipo) => {
    const map = { moldura: produtos.molduras, vidro: produtos.vidros, fundo: produtos.fundos, suplemento: produtos.suplementos };
    return map[tipo] || [];
  };

  if (showForm) {
    return (
      <div>
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2>Nova Ordem de Compra</h2>
          <button className="btn btn-secondary btn-sm" onClick={() => setShowForm(false)}>Cancelar</button>
        </header>

        <div className="card" style={{ marginBottom: '1rem' }}>
          <div className="form-group">
            <label>Fornecedor</label>
            <select className="input-control" value={form.fornecedor_id} onChange={e => setForm({ ...form, fornecedor_id: e.target.value })}>
              <option value="">Selecione...</option>
              {fornecedores.map(f => <option key={f.id} value={f.id}>{f.nome}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Observação</label>
            <input className="input-control" value={form.observacao} onChange={e => setForm({ ...form, observacao: e.target.value })} />
          </div>
        </div>

        {itens.map((item, i) => (
          <div key={i} className="card" style={{ marginBottom: '0.75rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr auto', gap: '0.75rem', alignItems: 'end' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Tipo</label>
                <select className="input-control" value={item.produto_tipo} onChange={e => { const novos = [...itens]; novos[i].produto_tipo = e.target.value; novos[i].produto_id = ''; setItens(novos); }}>
                  <option value="moldura">Moldura</option>
                  <option value="vidro">Vidro</option>
                  <option value="fundo">Fundo</option>
                  <option value="suplemento">Suplemento</option>
                </select>
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Produto</label>
                <select className="input-control" value={item.produto_id} onChange={e => { const novos = [...itens]; novos[i].produto_id = e.target.value; setItens(novos); }}>
                  <option value="">Selecione...</option>
                  {produtosDisponiveis(item.produto_tipo).map(p => (
                    <option key={p.id} value={p.id}>{p.codigo || p.nome || p.tipo}</option>
                  ))}
                </select>
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Qtd</label>
                <input type="number" className="input-control" value={item.quantidade_solicitada} min="1" onChange={e => { const novos = [...itens]; novos[i].quantidade_solicitada = e.target.value; setItens(novos); }} />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Preço Unit.</label>
                <input type="number" className="input-control" step="0.01" value={item.preco_unitario} onChange={e => { const novos = [...itens]; novos[i].preco_unitario = e.target.value; setItens(novos); }} />
              </div>
              <button className="btn-icon" onClick={() => setItens(itens.filter((_, idx) => idx !== i))} style={{ marginBottom: '0.5rem' }}><X size={18} /></button>
            </div>
          </div>
        ))}

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1rem' }}>
          <button className="btn btn-secondary btn-sm" onClick={() => setItens([...itens, { produto_tipo: 'moldura', produto_id: '', quantidade_solicitada: 1, preco_unitario: '' }])}>
            <Plus size={16} /> Adicionar Item
          </button>
          <button className="btn btn-primary btn-sm" onClick={criarOrdem}><Save size={16} /> Criar Ordem</button>
        </div>
      </div>
    );
  }

  if (showReceber) {
    return (
      <div className="modal-overlay" onClick={() => setShowReceber(null)}>
        <div className="modal-content" onClick={e => e.stopPropagation()}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h3>Receber Ordem #{showReceber.id}</h3>
            <button className="btn-icon" onClick={() => setShowReceber(null)}><X size={20} /></button>
          </div>
          {showReceber.itens.map(item => (
            <div key={item.id} style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '0.75rem' }}>
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: '0.9rem' }}>{TIPO_PRODUTO_LABEL[item.produto_tipo]} #{item.produto_id}</p>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Solicitado: {item.quantidade_solicitada} | Recebido: {item.quantidade_recebida}</p>
              </div>
              <input
                type="number"
                className="input-control"
                style={{ width: '100px' }}
                placeholder="Qtd"
                min="1"
                max={item.quantidade_solicitada - item.quantidade_recebida}
                value={receberQtds[item.id] || ''}
                onChange={e => setReceberQtds({ ...receberQtds, [item.id]: e.target.value })}
              />
            </div>
          ))}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1rem' }}>
            <button className="btn btn-secondary btn-sm" onClick={() => setShowReceber(null)}>Cancelar</button>
            <button className="btn btn-primary btn-sm" onClick={() => receberOrdem(showReceber.id)}>
              <CheckCircle size={16} /> Confirmar Recebimento
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <button className="btn btn-primary btn-sm" onClick={() => setShowForm(true)}>
          <Plus size={16} /> Nova Ordem
        </button>
      </div>

      {ordens.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
          Nenhuma ordem de compra registrada
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {ordens.map(o => (
            <div key={o.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <strong>Ordem #{o.id}</strong>
                    <span style={{
                      background: `${STATUS_CORES[o.status] || '#6b7280'}20`,
                      color: STATUS_CORES[o.status] || '#6b7280',
                      padding: '2px 8px', borderRadius: '10px', fontSize: '0.7rem', fontWeight: 600,
                    }}>
                      {o.status}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    {o.fornecedor?.nome || `Fornecedor #${o.fornecedor_id}`}
                  </p>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {o.itens?.length || 0} itens — {new Date(o.criado_em).toLocaleDateString('pt-BR')}
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  {o.status !== 'recebida' && o.status !== 'cancelada' && (
                    <button className="btn btn-primary btn-sm" onClick={() => setShowReceber(o)}>
                      <Package size={14} /> Receber
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const SugestoesTab = ({ sugestoes, onRefresh, onOrdemCriada }) => (
  <div>
    <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
      <button className="btn btn-secondary btn-sm" onClick={onRefresh}>
        <Clock size={16} /> Atualizar Sugestões
      </button>
    </div>

    {sugestoes.length === 0 ? (
      <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
        <CheckCircle size={32} style={{ marginBottom: '0.5rem', color: 'var(--accent-primary)' }} />
        <p>Estoque OK — nenhuma compra sugerida no momento</p>
      </div>
    ) : (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {sugestoes.map((s, i) => (
          <div key={i} className="card" style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <AlertTriangle size={18} color="#f59e0b" style={{ flexShrink: 0 }} />
            <div style={{ flex: 1 }}>
              <p style={{ fontWeight: 500, fontSize: '0.9rem' }}>{s.nome}</p>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                {s.motivo} — Sugerido: <strong>{s.quantidade_sugerida}</strong> un (atual: {s.quantidade_atual})
              </p>
            </div>
          </div>
        ))}
      </div>
    )}
  </div>
);

export default Compras;
