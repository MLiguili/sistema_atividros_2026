import React, { useState, useEffect, useCallback } from 'react';
import api from '../api/config';
import { Plus, DollarSign, CreditCard, TrendingDown, TrendingUp, AlertTriangle, CheckCircle, X } from 'lucide-react';

const STATUS_CORES = {
  pendente: '#f59e0b',
  parcial: '#8b5cf6',
  recebido: '#22c55e',
  pago: '#22c55e',
  cancelado: '#ef4444',
};

const Financeiro = () => {
  const [aba, setAba] = useState('receber');
  const [resumo, setResumo] = useState(null);
  const [contasReceber, setContasReceber] = useState([]);
  const [contasPagar, setContasPagar] = useState([]);
  const [fluxo, setFluxo] = useState([]);

  const carregarResumo = useCallback(async () => {
    try {
      const resp = await api.get('/financeiro/resumo');
      setResumo(resp.data);
    } catch (err) { console.error(err); }
  }, []);

  const carregarReceber = useCallback(async () => {
    try {
      const resp = await api.get('/financeiro/contas-receber');
      setContasReceber(resp.data);
    } catch (err) { console.error(err); }
  }, []);

  const carregarPagar = useCallback(async () => {
    try {
      const resp = await api.get('/financeiro/contas-pagar');
      setContasPagar(resp.data);
    } catch (err) { console.error(err); }
  }, []);

  const carregarFluxo = useCallback(async () => {
    try {
      const resp = await api.get('/financeiro/fluxo-caixa');
      setFluxo(resp.data);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { carregarResumo(); }, [carregarResumo]);
  useEffect(() => { if (aba === 'receber') carregarReceber(); }, [aba, carregarReceber]);
  useEffect(() => { if (aba === 'pagar') carregarPagar(); }, [aba, carregarPagar]);
  useEffect(() => { if (aba === 'fluxo') carregarFluxo(); }, [aba, carregarFluxo]);

  const formatValor = (v) => `R$ ${parseFloat(v || 0).toFixed(2)}`;

  return (
    <div className="financeiro-page fade-in">
      <header className="page-header">
        <h1>Financeiro</h1>
      </header>

      {resumo && (
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
          <ResumoCard label="A Receber" valor={resumo.total_a_receber} cor="#22c55e" icone={<TrendingUp size={18} />} />
          <ResumoCard label="Recebido" valor={resumo.total_recebido} cor="#16a34a" icone={<CheckCircle size={18} />} />
          <ResumoCard label="A Pagar" valor={resumo.total_a_pagar} cor="#ef4444" icone={<TrendingDown size={18} />} />
          <ResumoCard label="Pago" valor={resumo.total_pago} cor="#dc2626" icone={<CheckCircle size={18} />} />
          <ResumoCard
            label="Saldo Previsto"
            valor={resumo.saldo_previsto}
            cor={parseFloat(resumo.saldo_previsto) >= 0 ? '#22c55e' : '#ef4444'}
            icone={<DollarSign size={18} />}
          />
          <div className="card" style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: '120px' }}>
            <AlertTriangle size={18} color="#f59e0b" />
            <div>
              <p style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>Vencidas</p>
              <p style={{ fontSize: '0.9rem', fontWeight: 600, color: resumo.contas_receber_vencidas > 0 ? '#ef4444' : '#22c55e' }}>
                R: {resumo.contas_receber_vencidas} | P: {resumo.contas_pagar_vencidas}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="tabs">
        <button className={`tab ${aba === 'receber' ? 'active' : ''}`} onClick={() => setAba('receber')}>
          <TrendingUp size={16} /> A Receber
        </button>
        <button className={`tab ${aba === 'pagar' ? 'active' : ''}`} onClick={() => setAba('pagar')}>
          <TrendingDown size={16} /> A Pagar
        </button>
        <button className={`tab ${aba === 'fluxo' ? 'active' : ''}`} onClick={() => setAba('fluxo')}>
          <CreditCard size={16} /> Fluxo de Caixa
        </button>
      </div>

      {aba === 'receber' && <ContasReceberTab contas={contasReceber} onRefresh={carregarReceber} onResumoRefresh={carregarResumo} />}
      {aba === 'pagar' && <ContasPagarTab contas={contasPagar} onRefresh={carregarPagar} onResumoRefresh={carregarResumo} />}
      {aba === 'fluxo' && <FluxoTab fluxo={fluxo} onRefresh={carregarFluxo} />}
    </div>
  );
};

const ResumoCard = ({ label, valor, cor, icone }) => (
  <div className="card" style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: '120px' }}>
    <div style={{ color: cor }}>{icone}</div>
    <div>
      <p style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>{label}</p>
      <p style={{ fontSize: '0.9rem', fontWeight: 600, color: cor }}>R$ {parseFloat(valor || 0).toFixed(2)}</p>
    </div>
  </div>
);

const ContasReceberTab = ({ contas, onRefresh, onResumoRefresh }) => {
  const [showForm, setShowForm] = useState(false);
  const [showReceber, setShowReceber] = useState(null);
  const [form, setForm] = useState({ descricao: '', valor: '', data_vencimento: '', observacao: '' });
  const [receberValor, setReceberValor] = useState('');

  const criar = async () => {
    if (!form.descricao || !form.valor || !form.data_vencimento) return alert('Preencha descricao, valor e vencimento');
    try {
      await api.post('/financeiro/contas-receber', { ...form, valor: parseFloat(form.valor) });
      setShowForm(false);
      setForm({ descricao: '', valor: '', data_vencimento: '', observacao: '' });
      onRefresh();
      onResumoRefresh();
    } catch (err) { alert(err.response?.data?.detail || 'Erro'); }
  };

  const receber = async (contaId) => {
    if (!receberValor || parseFloat(receberValor) <= 0) return alert('Informe o valor recebido');
    try {
      await api.post(`/financeiro/contas-receber/${contaId}/receber`, { valor_recebido: parseFloat(receberValor) });
      setShowReceber(null);
      setReceberValor('');
      onRefresh();
      onResumoRefresh();
    } catch (err) { alert(err.response?.data?.detail || 'Erro'); }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <button className="btn btn-primary btn-sm" onClick={() => setShowForm(true)}><Plus size={16} /> Nova Conta</button>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group"><label>Descrição *</label><input className="input-control" value={form.descricao} onChange={e => setForm({ ...form, descricao: e.target.value })} /></div>
            <div className="form-group"><label>Valor *</label><input type="number" className="input-control" step="0.01" value={form.valor} onChange={e => setForm({ ...form, valor: e.target.value })} /></div>
            <div className="form-group"><label>Vencimento *</label><input type="date" className="input-control" value={form.data_vencimento} onChange={e => setForm({ ...form, data_vencimento: e.target.value })} /></div>
            <div className="form-group"><label>Observação</label><input className="input-control" value={form.observacao} onChange={e => setForm({ ...form, observacao: e.target.value })} /></div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
            <button className="btn btn-secondary btn-sm" onClick={() => setShowForm(false)}>Cancelar</button>
            <button className="btn btn-primary btn-sm" onClick={criar}>Criar Conta</button>
          </div>
        </div>
      )}

      {showReceber && (
        <div className="modal-overlay" onClick={() => setShowReceber(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '400px' }}>
            <h3 style={{ marginBottom: '1rem' }}>Receber: {showReceber.descricao}</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              Valor: R$ {parseFloat(showReceber.valor).toFixed(2)} | Recebido: R$ {parseFloat(showReceber.valor_recebido).toFixed(2)}
            </p>
            <div className="form-group"><label>Valor a Receber</label>
              <input type="number" className="input-control" step="0.01" value={receberValor} onChange={e => setReceberValor(e.target.value)} autoFocus />
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowReceber(null)}>Cancelar</button>
              <button className="btn btn-primary btn-sm" onClick={() => receber(showReceber.id)}>Confirmar</button>
            </div>
          </div>
        </div>
      )}

      {contas.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
          Nenhuma conta a receber
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {contas.map(c => (
            <div key={c.id} className="card" style={{ padding: '0.75rem 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <p style={{ fontWeight: 500, fontSize: '0.9rem' }}>{c.descricao}</p>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  Vence: {new Date(c.data_vencimento).toLocaleDateString('pt-BR')}
                  {c.pedido_id && ` | Pedido #${c.pedido_id}`}
                </p>
              </div>
              <div style={{ textAlign: 'right', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div>
                  <p style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>R$ {parseFloat(c.valor).toFixed(2)}</p>
                  <span style={{ background: `${STATUS_CORES[c.status]}20`, color: STATUS_CORES[c.status], padding: '1px 8px', borderRadius: '10px', fontSize: '0.7rem', fontWeight: 600 }}>
                    {c.status}
                  </span>
                </div>
                {c.status !== 'recebido' && c.status !== 'cancelado' && (
                  <button className="btn btn-primary btn-sm" onClick={() => { setShowReceber(c); setReceberValor(''); }}>
                    <DollarSign size={14} /> Receber
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const ContasPagarTab = ({ contas, onRefresh, onResumoRefresh }) => {
  const [showForm, setShowForm] = useState(false);
  const [showPagar, setShowPagar] = useState(null);
  const [form, setForm] = useState({ descricao: '', valor: '', data_vencimento: '', observacao: '' });
  const [pagarValor, setPagarValor] = useState('');

  const criar = async () => {
    if (!form.descricao || !form.valor || !form.data_vencimento) return alert('Preencha descricao, valor e vencimento');
    try {
      await api.post('/financeiro/contas-pagar', { ...form, valor: parseFloat(form.valor) });
      setShowForm(false);
      setForm({ descricao: '', valor: '', data_vencimento: '', observacao: '' });
      onRefresh();
      onResumoRefresh();
    } catch (err) { alert(err.response?.data?.detail || 'Erro'); }
  };

  const pagar = async (contaId) => {
    if (!pagarValor || parseFloat(pagarValor) <= 0) return alert('Informe o valor pago');
    try {
      await api.post(`/financeiro/contas-pagar/${contaId}/pagar`, { valor_pago: parseFloat(pagarValor) });
      setShowPagar(null);
      setPagarValor('');
      onRefresh();
      onResumoRefresh();
    } catch (err) { alert(err.response?.data?.detail || 'Erro'); }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <button className="btn btn-primary btn-sm" onClick={() => setShowForm(true)}><Plus size={16} /> Nova Conta</button>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group"><label>Descrição *</label><input className="input-control" value={form.descricao} onChange={e => setForm({ ...form, descricao: e.target.value })} /></div>
            <div className="form-group"><label>Valor *</label><input type="number" className="input-control" step="0.01" value={form.valor} onChange={e => setForm({ ...form, valor: e.target.value })} /></div>
            <div className="form-group"><label>Vencimento *</label><input type="date" className="input-control" value={form.data_vencimento} onChange={e => setForm({ ...form, data_vencimento: e.target.value })} /></div>
            <div className="form-group"><label>Observação</label><input className="input-control" value={form.observacao} onChange={e => setForm({ ...form, observacao: e.target.value })} /></div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
            <button className="btn btn-secondary btn-sm" onClick={() => setShowForm(false)}>Cancelar</button>
            <button className="btn btn-primary btn-sm" onClick={criar}>Criar Conta</button>
          </div>
        </div>
      )}

      {showPagar && (
        <div className="modal-overlay" onClick={() => setShowPagar(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '400px' }}>
            <h3 style={{ marginBottom: '1rem' }}>Pagar: {showPagar.descricao}</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              Valor: R$ {parseFloat(showPagar.valor).toFixed(2)} | Pago: R$ {parseFloat(showPagar.valor_pago).toFixed(2)}
            </p>
            <div className="form-group"><label>Valor a Pagar</label>
              <input type="number" className="input-control" step="0.01" value={pagarValor} onChange={e => setPagarValor(e.target.value)} autoFocus />
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowPagar(null)}>Cancelar</button>
              <button className="btn btn-primary btn-sm" onClick={() => pagar(showPagar.id)}>Confirmar</button>
            </div>
          </div>
        </div>
      )}

      {contas.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
          Nenhuma conta a pagar
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {contas.map(c => (
            <div key={c.id} className="card" style={{ padding: '0.75rem 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <p style={{ fontWeight: 500, fontSize: '0.9rem' }}>{c.descricao}</p>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  Vence: {new Date(c.data_vencimento).toLocaleDateString('pt-BR')}
                </p>
              </div>
              <div style={{ textAlign: 'right', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div>
                  <p style={{ fontWeight: 600, color: '#ef4444' }}>R$ {parseFloat(c.valor).toFixed(2)}</p>
                  <span style={{ background: `${STATUS_CORES[c.status]}20`, color: STATUS_CORES[c.status], padding: '1px 8px', borderRadius: '10px', fontSize: '0.7rem', fontWeight: 600 }}>
                    {c.status}
                  </span>
                </div>
                {c.status !== 'pago' && c.status !== 'cancelado' && (
                  <button className="btn btn-primary btn-sm" onClick={() => { setShowPagar(c); setPagarValor(''); }}>
                    <DollarSign size={14} /> Pagar
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const FluxoTab = ({ fluxo, onRefresh }) => (
  <div>
    <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
      <button className="btn btn-secondary btn-sm" onClick={onRefresh}>Atualizar</button>
    </div>

    {fluxo.length === 0 ? (
      <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
        Nenhum lançamento no período
      </div>
    ) : (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {fluxo.map((l, i) => (
          <div key={i} className="card" style={{ padding: '0.75rem 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              {l.tipo === 'receita' ? <TrendingUp size={18} color="#22c55e" /> : <TrendingDown size={18} color="#ef4444" />}
              <div>
                <p style={{ fontWeight: 500, fontSize: '0.9rem' }}>{l.descricao}</p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  {new Date(l.data).toLocaleDateString('pt-BR')} — {l.tipo === 'receita' ? 'Receita' : 'Despesa'}
                </p>
              </div>
            </div>
            <p style={{ fontWeight: 600, color: l.tipo === 'receita' ? '#22c55e' : '#ef4444' }}>
              {l.tipo === 'receita' ? '+' : '-'} R$ {parseFloat(l.valor).toFixed(2)}
            </p>
          </div>
        ))}
        <div className="card" style={{ padding: '0.75rem 1rem', display: 'flex', justifyContent: 'space-between', background: 'rgba(255,255,255,0.03)' }}>
          <strong>Saldo do Período</strong>
          <strong style={{ color: fluxo.reduce((acc, l) => acc + (l.tipo === 'receita' ? parseFloat(l.valor) : -parseFloat(l.valor)), 0) >= 0 ? '#22c55e' : '#ef4444' }}>
            R$ {fluxo.reduce((acc, l) => acc + (l.tipo === 'receita' ? parseFloat(l.valor) : -parseFloat(l.valor)), 0).toFixed(2)}
          </strong>
        </div>
      </div>
    )}
  </div>
);

export default Financeiro;
