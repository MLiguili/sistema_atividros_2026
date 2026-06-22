import React, { useState, useEffect } from 'react';
import api from '../api/config';
import { Plus, Trash2, X, UserPlus, Send, FileText, CheckCircle } from 'lucide-react';

const ModalNovoPedido = ({ onFechar, onCriado }) => {
  const [clientes, setClientes] = useState([]);
  const [materiais, setMateriais] = useState({ molduras: [], vidros: [], fundos: [] });
  const [criado, setCriado] = useState(null);
  const [modalNovoCliente, setModalNovoCliente] = useState(false);
  const [novoCliente, setNovoCliente] = useState({ nome: '', sobrenome: '', telefone: '', email: '', endereco: '', cep: '' });
  const [pedido, setPedido] = useState({
    cliente_id: '',
    itens: [{ moldura_id: '', vidro_id: '', fundo_id: '', largura: 30, altura: 40, quantidade: 1, preco_unitario: 0, descricao: '' }],
    valor_sinal: 0,
    endereco_entrega: '',
    frete: 0
  });

  useEffect(() => {
    const carregar = async () => {
      try {
        const [c, m, v, f] = await Promise.all([
          api.get('/clientes/'),
          api.get('/estoque/molduras'),
          api.get('/estoque/vidros'),
          api.get('/estoque/fundos')
        ]);
        setClientes(c.data);
        setMateriais({ molduras: m.data, vidros: v.data, fundos: f.data });
      } catch (erro) {
        console.error('Erro ao carregar dados:', erro);
      }
    };
    carregar();
  }, []);

  const calcularPrecoItem = async (index) => {
    const item = pedido.itens[index];
    if (!item.largura || !item.altura) return;
    try {
      const resposta = await api.post('/calculadora/simular', {
        largura: parseFloat(item.largura),
        altura: parseFloat(item.altura),
        quantidade: parseInt(item.quantidade),
        moldura_id: item.moldura_id || null,
        vidro_id: item.vidro_id || null,
        fundo_id: item.fundo_id || null
      });
      const novosItens = [...pedido.itens];
      novosItens[index].preco_unitario = parseFloat(resposta.data.total_estimado) / item.quantidade;
      setPedido({ ...pedido, itens: novosItens });
    } catch {
      console.warn('Erro ao calcular item');
    }
  };

  const atualizarItem = (index, campo, valor) => {
    const novosItens = [...pedido.itens];
    novosItens[index][campo] = valor;
    setPedido({ ...pedido, itens: novosItens });
    if (['largura', 'altura', 'moldura_id', 'vidro_id', 'fundo_id', 'quantidade'].includes(campo)) {
      calcularPrecoItem(index);
    }
  };

  const adicionarItem = () => {
    setPedido({
      ...pedido,
      itens: [...pedido.itens, { moldura_id: '', vidro_id: '', fundo_id: '', largura: 30, altura: 40, quantidade: 1, preco_unitario: 0, descricao: '' }]
    });
  };

  const removerItem = (index) => {
    if (pedido.itens.length === 1) return;
    const novosItens = pedido.itens.filter((_, i) => i !== index);
    setPedido({ ...pedido, itens: novosItens });
  };

  const finalizarPedido = async () => {
    if (!pedido.cliente_id) return alert('Selecione um cliente!');
    try {
      const resposta = await api.post('/pedidos/', {
        cliente_id: parseInt(pedido.cliente_id),
        itens: pedido.itens.map(item => ({
          ...item,
          largura: parseFloat(item.largura),
          altura: parseFloat(item.altura),
          quantidade: parseInt(item.quantidade),
          preco_unitario: parseFloat(item.preco_unitario),
          moldura_id: item.moldura_id ? parseInt(item.moldura_id) : null,
          vidro_id: item.vidro_id ? parseInt(item.vidro_id) : null,
          fundo_id: item.fundo_id ? parseInt(item.fundo_id) : null
        })),
        valor_sinal: parseFloat(pedido.valor_sinal) || 0,
        endereco_entrega: pedido.endereco_entrega,
        frete: parseFloat(pedido.frete) || 0
      });
      setCriado(resposta.data);
    } catch (erro) {
      alert('Erro ao criar pedido: ' + (erro.response?.data?.detail || erro.message));
    }
  };

  const criarCliente = async () => {
    if (!novoCliente.nome || !novoCliente.sobrenome || !novoCliente.telefone) {
      return alert('Nome, sobrenome e telefone sao obrigatorios.');
    }
    try {
      const resposta = await api.post('/clientes/', novoCliente);
      const [c] = await Promise.all([api.get('/clientes/')]);
      setClientes(c.data);
      setPedido({ ...pedido, cliente_id: resposta.data.id.toString() });
      setModalNovoCliente(false);
      setNovoCliente({ nome: '', sobrenome: '', telefone: '', email: '', endereco: '', cep: '' });
    } catch (erro) {
      alert('Erro ao criar cliente: ' + (erro.response?.data?.detail || erro.message));
    }
  };

  const baixarPDF = async (id) => {
    try {
      const resposta = await api.get(`/pedidos/${id}/pdf`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([resposta.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `pedido_${id}.pdf`);
      document.body.appendChild(link);
      link.click();
    } catch { console.error('Erro ao baixar PDF'); }
  };

  if (criado) {
    return (
      <div className="modal-overlay" onClick={onFechar}>
        <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '450px', textAlign: 'center', padding: '2rem' }}>
          <CheckCircle size={64} color="var(--accent-primary)" style={{ marginBottom: '1.5rem' }} />
          <h2>Pedido #{criado.numero_pedido} Criado!</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>O pedido foi registrado no sistema.</p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button className="btn btn-primary" onClick={() => baixarPDF(criado.id)}>
              <FileText size={20} /> Baixar PDF
            </button>
            <button className="btn btn-secondary" onClick={() => { onCriado(); onFechar(); }}>
              Fechar
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onFechar}>
      <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '800px', maxHeight: '90vh', overflowY: 'auto' }}>
        <div className="modal-header">
          <h2>Novo Pedido</h2>
          <button className="btn-icon" onClick={onFechar}><X size={20} /></button>
        </div>

        <div className="card" style={{ marginBottom: '1rem', padding: '1rem' }}>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
            <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
              <label>Cliente *</label>
              <select className="input-control" value={pedido.cliente_id} onChange={(e) => setPedido({ ...pedido, cliente_id: e.target.value })}>
                <option value="">Selecione...</option>
                {clientes.map(c => <option key={c.id} value={c.id}>{c.nome} {c.sobrenome}</option>)}
              </select>
            </div>
            <button className="btn btn-secondary" onClick={() => setModalNovoCliente(true)} title="Novo Cliente">
              <UserPlus size={20} /> Novo
            </button>
          </div>
        </div>

        {pedido.itens.map((item, index) => (
          <div key={index} className="card" style={{ padding: '1rem', marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
              <h3>Item #{index + 1}</h3>
              {pedido.itens.length > 1 && (
                <button className="btn-icon" onClick={() => removerItem(index)}>
                  <Trash2 size={18} color="var(--danger)" />
                </button>
              )}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.75rem' }}>
              <div className="form-group">
                <label>Moldura</label>
                <select className="input-control" value={item.moldura_id} onChange={(e) => atualizarItem(index, 'moldura_id', e.target.value)}>
                  <option value="">Nenhuma</option>
                  {materiais.molduras.map(m => <option key={m.id} value={m.id}>{m.codigo} - {m.cor}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Vidro</label>
                <select className="input-control" value={item.vidro_id} onChange={(e) => atualizarItem(index, 'vidro_id', e.target.value)}>
                  <option value="">Nenhum</option>
                  {materiais.vidros.map(v => <option key={v.id} value={v.id}>{v.tipo}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Fundo</label>
                <select className="input-control" value={item.fundo_id} onChange={(e) => atualizarItem(index, 'fundo_id', e.target.value)}>
                  <option value="">Nenhum</option>
                  {materiais.fundos.map(f => <option key={f.id} value={f.id}>{f.tipo}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Largura</label>
                <input type="number" className="input-control" value={item.largura} onChange={(e) => atualizarItem(index, 'largura', e.target.value)} />
              </div>
              <div className="form-group">
                <label>Altura</label>
                <input type="number" className="input-control" value={item.altura} onChange={(e) => atualizarItem(index, 'altura', e.target.value)} />
              </div>
              <div className="form-group">
                <label>Qtd</label>
                <input type="number" className="input-control" value={item.quantidade} onChange={(e) => atualizarItem(index, 'quantidade', e.target.value)} />
              </div>
              <div className="form-group">
                <label>Preço Unit.</label>
                <input type="number" className="input-control" value={item.preco_unitario} onChange={(e) => atualizarItem(index, 'preco_unitario', e.target.value)} step="0.01" />
              </div>
              <div className="form-group">
                <label>Subtotal</label>
                <div style={{ padding: '0.5rem', background: 'rgba(255,255,255,0.05)', borderRadius: '6px', textAlign: 'right', fontWeight: 'bold', marginTop: '0.25rem' }}>
                  R$ {(item.preco_unitario * item.quantidade).toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        ))}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem' }}>
          <button className="btn btn-secondary" onClick={adicionarItem}>
            <Plus size={20} /> Adicionar Item
          </button>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <div style={{ textAlign: 'right' }}>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Total</p>
              <h2 style={{ color: 'var(--accent-primary)' }}>
                R$ {pedido.itens.reduce((acc, curr) => acc + (curr.preco_unitario * curr.quantidade), 0).toFixed(2)}
              </h2>
            </div>
            <button className="btn btn-primary" onClick={finalizarPedido}>
              <Send size={20} /> Criar Pedido
            </button>
          </div>
        </div>
      </div>

      {modalNovoCliente && (
        <div className="modal-overlay" onClick={() => setModalNovoCliente(false)} style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1100 }}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '500px' }}>
            <div className="modal-header">
              <h2>Novo Cliente</h2>
              <button className="btn-icon" onClick={() => setModalNovoCliente(false)}><X size={20} /></button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '0.75rem' }}>
              <div className="form-group">
                <label>Nome *</label>
                <input type="text" className="input-control" value={novoCliente.nome} onChange={(e) => setNovoCliente({ ...novoCliente, nome: e.target.value })} placeholder="Primeiro nome" />
              </div>
              <div className="form-group">
                <label>Sobrenome *</label>
                <input type="text" className="input-control" value={novoCliente.sobrenome} onChange={(e) => setNovoCliente({ ...novoCliente, sobrenome: e.target.value })} placeholder="Sobrenome" />
              </div>
            </div>
            <div className="form-group" style={{ marginBottom: '0.75rem' }}>
              <label>Telefone *</label>
              <input type="text" className="input-control" value={novoCliente.telefone} onChange={(e) => setNovoCliente({ ...novoCliente, telefone: e.target.value })} placeholder="(11) 99999-9999" />
            </div>
            <div className="form-group" style={{ marginBottom: '0.75rem' }}>
              <label>Email</label>
              <input type="email" className="input-control" value={novoCliente.email} onChange={(e) => setNovoCliente({ ...novoCliente, email: e.target.value })} placeholder="email@exemplo.com" />
            </div>
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label>Endereço</label>
              <input type="text" className="input-control" value={novoCliente.endereco} onChange={(e) => setNovoCliente({ ...novoCliente, endereco: e.target.value })} placeholder="Rua, número, bairro" />
            </div>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setModalNovoCliente(false)}>Cancelar</button>
              <button className="btn btn-primary" onClick={criarCliente}><UserPlus size={18} /> Cadastrar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModalNovoPedido;
