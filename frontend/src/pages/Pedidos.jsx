import React, { useState, useEffect } from 'react';
import api from '../api/config';
import { Plus, Trash2, FileText, Send, CheckCircle, X, Clock, AlertTriangle, ChevronRight, History, UserPlus, LayoutGrid, List } from 'lucide-react';

const Pedidos = () => {
  const [pedidos, setPedidos] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [materiais, setMateriais] = useState({ molduras: [], vidros: [], fundos: [] });
  const [criado, setCriado] = useState(null);
  const [pedidoDetalhe, setPedidoDetalhe] = useState(null);
  const [visualizacao, setVisualizacao] = useState('kanban');
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [pedido, setPedido] = useState({
    cliente_id: '',
    itens: [{ moldura_id: '', vidro_id: '', fundo_id: '', largura: 30, altura: 40, quantidade: 1, preco_unitario: 0, descricao: '' }],
    valor_sinal: 0,
    endereco_entrega: '',
    frete: 0
  });
  const [modalSinal, setModalSinal] = useState(null);
  const [modalNovoCliente, setModalNovoCliente] = useState(false);
  const [novoCliente, setNovoCliente] = useState({ nome: '', sobrenome: '', telefone: '', email: '', endereco: '', cep: '' });
  const [modalBaixaEstoque, setModalBaixaEstoque] = useState(null);

  const carregarDados = async () => {
    try {
      const [p, c, m, v, f] = await Promise.all([
        api.get('/pedidos/'),
        api.get('/clientes/'),
        api.get('/estoque/molduras'),
        api.get('/estoque/vidros'),
        api.get('/estoque/fundos')
      ]);
      setPedidos(p.data);
      setClientes(c.data);
      setMateriais({ molduras: m.data, vidros: v.data, fundos: f.data });
    } catch (erro) {
      console.error('Erro ao carregar dados:', erro);
    }
  };

  useEffect(() => {
    carregarDados();
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
    } catch (erro) {
      console.warn('Erro ao calcular item:', erro);
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
      carregarDados();
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
      await carregarDados();
      setPedido({ ...pedido, cliente_id: resposta.data.id.toString() });
      setModalNovoCliente(false);
      setNovoCliente({ nome: '', sobrenome: '', telefone: '', email: '', endereco: '', cep: '' });
    } catch (erro) {
      alert('Erro ao criar cliente: ' + (erro.response?.data?.detail || erro.message));
    }
  };

  const confirmarBaixaEstoque = async () => {
    if (!modalBaixaEstoque) return;
    try {
      await api.post(`/pedidos/${modalBaixaEstoque.id}/baixa-estoque`);
      setModalBaixaEstoque(null);
      carregarDados();
      if (pedidoDetalhe && pedidoDetalhe.id === modalBaixaEstoque.id) {
        const resposta = await api.get(`/pedidos/${modalBaixaEstoque.id}`);
        setPedidoDetalhe(resposta.data);
      }
    } catch (erro) {
      alert('Erro ao dar baixa no estoque: ' + (erro.response?.data?.detail || erro.message));
    }
  };

  const atualizarStatus = async (pedidoId, eixo, novoStatus, valorSinal = null) => {
    try {
      const payload = { eixo, novo_status: novoStatus };
      if (valorSinal !== null) {
        payload.valor_sinal = valorSinal;
      }
      await api.patch(`/pedidos/${pedidoId}/status`, payload);
      carregarDados();
      if (pedidoDetalhe && pedidoDetalhe.id === pedidoId) {
        const resposta = await api.get(`/pedidos/${pedidoId}`);
        setPedidoDetalhe(resposta.data);
      }
    } catch (erro) {
      alert('Erro ao atualizar status: ' + (erro.response?.data?.detail || erro.message));
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
    } catch (erro) {
      console.error('Erro ao baixar PDF:', erro);
    }
  };

  const getStatusBadge = (status, tipo) => {
    const cores = {
      geral: { rascunho: '#6b7280', confirmado: '#6366f1', cancelado: '#ef4444', entregue: '#22c55e', arquivado: '#9ca3af' },
      producao: { pendente: '#f59e0b', aguardando_material: '#f97316', em_producao: '#8b5cf6', para_embalar: '#06b6d4', pronto_entrega: '#10b981', entregue: '#22c55e' },
      financeiro: { sem_pagamento: '#ef4444', sinal_recebido: '#f59e0b', pago_total: '#22c55e', estornado: '#dc2626' }
    };
    const labels = {
      geral: { rascunho: 'Rascunho', confirmado: 'Confirmado', cancelado: 'Cancelado', entregue: 'Entregue', arquivado: 'Arquivado' },
      producao: { pendente: 'Pendente', aguardando_material: 'Aguardando Material', em_producao: 'Em Produção', para_embalar: 'Para Embalar', pronto_entrega: 'Pronto', entregue: 'Entregue' },
      financeiro: { sem_pagamento: 'Sem Pgto', sinal_recebido: 'Sinal', pago_total: 'Pago', estornado: 'Estornado' }
    };
    return (
      <span style={{ 
        background: cores[tipo]?.[status] || '#6b7280', 
        color: 'white', 
        padding: '2px 8px', 
        borderRadius: '12px', 
        fontSize: '0.7rem',
        fontWeight: 500
      }}>
        {labels[tipo]?.[status] || status}
      </span>
    );
  };

  if (criado) {
    return (
      <div className="pedidos-page fade-in">
        <div className="card fade-in" style={{ textAlign: 'center', padding: '3rem' }}>
          <CheckCircle size={64} color="var(--accent-primary)" style={{ marginBottom: '1.5rem' }} />
          <h2>Pedido #{criado.numero_pedido} Criado!</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
            O pedido foi registrado no sistema.
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button className="btn btn-primary" onClick={() => baixarPDF(criado.id)}>
              <FileText size={20} /> Baixar PDF
            </button>
            <button className="btn btn-glass" onClick={() => { setCriado(null); setMostrarFormulario(false); }}>
              Ver Pedidos
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (modalSinal) {
    return (
      <div className="modal-overlay" onClick={() => setModalSinal(null)} style={{
        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
        background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center',
        justifyContent: 'center', zIndex: 1000
      }}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{
          background: 'var(--card-bg)', padding: '2rem', borderRadius: '12px',
          width: '90%', maxWidth: '400px', border: '1px solid var(--glass-border)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2>Receber Sinal</h2>
            <button className="btn btn-icon" onClick={() => setModalSinal(null)}>
              <X size={20} />
            </button>
          </div>
          
          <div style={{ marginBottom: '1.5rem' }}>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Informe o valor do sinal a receber. O valor nao pode exceder o total do pedido.
            </p>
            <div className="form-group">
              <label>Valor do Sinal (R$)</label>
              <input
                type="number"
                className="input-control"
                value={modalSinal.valorSinal}
                onChange={(e) => setModalSinal({ ...modalSinal, valorSinal: e.target.value })}
                placeholder="0.00"
                step="0.01"
                min="0"
                max={modalSinal.valorTotal}
                autoFocus
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <span>Total do pedido:</span>
              <span>R$ {modalSinal.valorTotal.toFixed(2)}</span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
            <button className="btn btn-glass" onClick={() => setModalSinal(null)}>
              Cancelar
            </button>
            <button
              className="btn btn-primary"
              onClick={() => {
                const valor = parseFloat(modalSinal.valorSinal);
                if (isNaN(valor) || valor <= 0) {
                  alert('Informe um valor valido maior que zero.');
                  return;
                }
                if (valor > modalSinal.valorTotal) {
                  alert('O valor do sinal nao pode exceder o total do pedido.');
                  return;
                }
                atualizarStatus(modalSinal.pedidoId, 'financeiro', 'sinal_recebido', valor);
                setModalSinal(null);
              }}
            >
              Confirmar
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (modalNovoCliente) {
    return (
      <div className="modal-overlay" onClick={() => setModalNovoCliente(false)} style={{
        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
        background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center',
        justifyContent: 'center', zIndex: 1000
      }}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{
          background: 'var(--card-bg)', padding: '2rem', borderRadius: '12px',
          width: '90%', maxWidth: '500px', border: '1px solid var(--glass-border)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2>Novo Cliente</h2>
            <button className="btn btn-icon" onClick={() => setModalNovoCliente(false)}>
              <X size={20} />
            </button>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div className="form-group">
              <label>Nome *</label>
              <input
                type="text"
                className="input-control"
                value={novoCliente.nome}
                onChange={(e) => setNovoCliente({ ...novoCliente, nome: e.target.value })}
                placeholder="Primeiro nome"
              />
            </div>
            <div className="form-group">
              <label>Sobrenome *</label>
              <input
                type="text"
                className="input-control"
                value={novoCliente.sobrenome}
                onChange={(e) => setNovoCliente({ ...novoCliente, sobrenome: e.target.value })}
                placeholder="Sobrenome"
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: '1rem' }}>
            <label>Telefone *</label>
            <input
              type="text"
              className="input-control"
              value={novoCliente.telefone}
              onChange={(e) => setNovoCliente({ ...novoCliente, telefone: e.target.value })}
              placeholder="(11) 99999-9999"
            />
          </div>

          <div className="form-group" style={{ marginBottom: '1rem' }}>
            <label>Email</label>
            <input
              type="email"
              className="input-control"
              value={novoCliente.email}
              onChange={(e) => setNovoCliente({ ...novoCliente, email: e.target.value })}
              placeholder="email@exemplo.com"
            />
          </div>

          <div className="form-group" style={{ marginBottom: '1rem' }}>
            <label>Endereco</label>
            <input
              type="text"
              className="input-control"
              value={novoCliente.endereco}
              onChange={(e) => setNovoCliente({ ...novoCliente, endereco: e.target.value })}
              placeholder="Rua, numero, bairro"
            />
          </div>

          <div className="form-group" style={{ marginBottom: '1.5rem' }}>
            <label>CEP</label>
            <input
              type="text"
              className="input-control"
              value={novoCliente.cep}
              onChange={(e) => setNovoCliente({ ...novoCliente, cep: e.target.value })}
              placeholder="00000-000"
            />
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
            <button className="btn btn-glass" onClick={() => setModalNovoCliente(false)}>
              Cancelar
            </button>
            <button className="btn btn-primary" onClick={criarCliente}>
              <UserPlus size={18} /> Cadastrar Cliente
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (modalBaixaEstoque) {
    return (
      <div className="modal-overlay" onClick={() => setModalBaixaEstoque(null)} style={{
        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
        background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center',
        justifyContent: 'center', zIndex: 1000
      }}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{
          background: 'var(--card-bg)', padding: '2rem', borderRadius: '12px',
          width: '90%', maxWidth: '450px', border: '1px solid var(--glass-border)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2>Confirmar Baixa de Estoque</h2>
            <button className="btn btn-icon" onClick={() => setModalBaixaEstoque(null)}>
              <X size={20} />
            </button>
          </div>
          
          <div style={{ marginBottom: '1.5rem' }}>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Ao confirmar, sera dado baixa no estoque dos seguintes itens:
            </p>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px' }}>
              {modalBaixaEstoque.itens?.map((item, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                  <span>{item.descricao}</span>
                  <span style={{ color: 'var(--accent-primary)' }}>x{item.quantidade}</span>
                </div>
              ))}
            </div>
            <p style={{ color: 'var(--warning)', fontSize: '0.85rem', marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertTriangle size={16} /> Essa acao nao pode ser desfeita.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
            <button className="btn btn-glass" onClick={() => setModalBaixaEstoque(null)}>
              Cancelar
            </button>
            <button className="btn btn-primary" onClick={confirmarBaixaEstoque}>
              Confirmar Baixa
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (pedidoDetalhe) {
    return (
      <div className="pedidos-page fade-in">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <div>
            <h1>Pedido #{pedidoDetalhe.numero_pedido}</h1>
            <p style={{ color: 'var(--text-secondary)' }}>
              {pedidoDetalhe.cliente?.nome} {pedidoDetalhe.cliente?.sobrenome}
            </p>
          </div>
          <button className="btn btn-glass" onClick={() => setPedidoDetalhe(null)}>
            <X size={20} /> Fechar
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
          <div>
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1rem' }}>Status do Pedido</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <span style={{ width: '100px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Geral:</span>
                  {getStatusBadge(pedidoDetalhe.status_geral, 'geral')}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <span style={{ width: '100px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Produção:</span>
                  {getStatusBadge(pedidoDetalhe.status_producao, 'producao')}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <span style={{ width: '100px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Financeiro:</span>
                  {getStatusBadge(pedidoDetalhe.status_financeiro, 'financeiro')}
                </div>
              </div>
            </div>

            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1rem' }}>Itens</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--glass-border)' }}>
                    <th style={{ textAlign: 'left', padding: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Descrição</th>
                    <th style={{ textAlign: 'center', padding: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Qtd</th>
                    <th style={{ textAlign: 'right', padding: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Unitário</th>
                    <th style={{ textAlign: 'right', padding: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Subtotal</th>
                  </tr>
                </thead>
                <tbody>
                  {pedidoDetalhe.itens.map(item => (
                    <tr key={item.id} style={{ borderBottom: '1px solid var(--glass-border)' }}>
                      <td style={{ padding: '0.75rem' }}>{item.descricao}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'center' }}>{item.quantidade}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'right' }}>R$ {parseFloat(item.preco_unitario).toFixed(2)}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'right' }}>R$ {parseFloat(item.subtotal).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1rem' }}>Valores</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Total:</span>
                  <span>R$ {parseFloat(pedidoDetalhe.valor_total).toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Sinal:</span>
                  <span>R$ {parseFloat(pedidoDetalhe.valor_sinal).toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold' }}>
                  <span>Saldo:</span>
                  <span style={{ color: pedidoDetalhe.saldo_devedor > 0 ? 'var(--danger)' : 'var(--accent-primary)' }}>
                    R$ {parseFloat(pedidoDetalhe.saldo_devedor).toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1rem' }}>Ações Rápidas</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {pedidoDetalhe.status_geral === 'rascunho' && (
                  <button className="btn btn-primary" onClick={() => atualizarStatus(pedidoDetalhe.id, 'geral', 'confirmado')}>
                    Confirmar Pedido
                  </button>
                )}
                {pedidoDetalhe.status_geral === 'confirmado' && (
                  <button className="btn btn-primary" onClick={() => atualizarStatus(pedidoDetalhe.id, 'geral', 'entregue')}>
                    Marcar Entregue
                  </button>
                )}
                {['pendente', 'aguardando_material'].includes(pedidoDetalhe.status_producao) && (
                  <button className="btn btn-primary" onClick={() => setModalBaixaEstoque(pedidoDetalhe)}>
                    Dar Baixa no Estoque
                  </button>
                )}
                {['rascunho', 'confirmado'].includes(pedidoDetalhe.status_geral) && (
                  <button 
                    className="btn" 
                    style={{ background: 'var(--danger)', color: 'white' }} 
                    onClick={() => {
                      if (pedidoDetalhe.status_financeiro === 'sinal_recebido') {
                        if (!confirm('Este pedido tem sinal recebido. O cancelamento ira estornar o sinal automaticamente. Deseja continuar?')) return;
                      }
                      atualizarStatus(pedidoDetalhe.id, 'geral', 'cancelado');
                    }}
                  >
                    Cancelar
                  </button>
                )}
                {pedidoDetalhe.status_financeiro === 'sem_pagamento' && (
                  <button className="btn btn-glass" onClick={() => setModalSinal({ pedidoId: pedidoDetalhe.id, valorTotal: parseFloat(pedidoDetalhe.valor_total), valorSinal: '' })}>
                    Receber Sinal
                  </button>
                )}
                {pedidoDetalhe.status_financeiro === 'sinal_recebido' && (
                  <button className="btn btn-glass" onClick={() => atualizarStatus(pedidoDetalhe.id, 'financeiro', 'pago_total')}>
                    Quitar
                  </button>
                )}
                <button className="btn btn-glass" onClick={() => baixarPDF(pedidoDetalhe.id)}>
                  <FileText size={18} /> Baixar PDF
                </button>
                <div style={{ marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid var(--glass-border)' }}>
                  <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem', display: 'block' }}>
                    Status de Produção
                  </label>
                  <select 
                    className="input-control"
                    value={pedidoDetalhe.status_producao}
                    onChange={(e) => atualizarStatus(pedidoDetalhe.id, 'producao', e.target.value)}
                    style={{ width: '100%' }}
                  >
                    <option value="pendente">Pendente</option>
                    <option value="aguardando_material">Aguardando Material</option>
                    <option value="em_producao">Em Produção</option>
                    <option value="para_embalar">Para Embalar</option>
                    <option value="pronto_entrega">Pronto para Entrega</option>
                    <option value="entregue">Entregue</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="card">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <History size={18} /> Histórico
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '300px', overflowY: 'auto' }}>
                {pedidoDetalhe.eventos?.length > 0 ? (
                  pedidoDetalhe.eventos.map(evento => (
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
                        <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic', marginTop: '0.25rem' }}>
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
      </div>
    );
  }

  if (mostrarFormulario) {
    return (
      <div className="pedidos-page fade-in">
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h1>Novo Pedido</h1>
          <button className="btn btn-glass" onClick={() => setMostrarFormulario(false)}>
            Cancelar
          </button>
        </header>

        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
            <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
              <label>Cliente *</label>
              <select 
                className="input-control" 
                value={pedido.cliente_id} 
                onChange={(e) => setPedido({ ...pedido, cliente_id: e.target.value })}
              >
                <option value="">Selecione...</option>
                {clientes.map(c => (
                  <option key={c.id} value={c.id}>{c.nome} {c.sobrenome}</option>
                ))}
              </select>
            </div>
            <button className="btn btn-glass" onClick={() => setModalNovoCliente(true)} title="Novo Cliente">
              <UserPlus size={20} /> Novo Cliente
            </button>
          </div>
        </div>

        <div className="itens-wrapper" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {pedido.itens.map((item, index) => (
            <div key={index} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <h3>Item #{index + 1}</h3>
                <button 
                  className="btn-icon" 
                  onClick={() => removerItem(index)}
                  style={{ visibility: pedido.itens.length > 1 ? 'visible' : 'hidden' }}
                >
                  <Trash2 size={18} color="var(--danger)" />
                </button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
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
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1rem', marginTop: '1rem' }}>
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
                  <div style={{ padding: '0.5rem', background: 'rgba(255,255,255,0.05)', borderRadius: '6px', textAlign: 'right', fontWeight: 'bold' }}>
                    R$ {(item.preco_unitario * item.quantidade).toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '2rem' }}>
          <button className="btn btn-glass" onClick={adicionarItem}>
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
    );
  }

  const colunasKanban = [
    { key: 'pendente', label: 'Pendente', cor: '#f59e0b' },
    { key: 'aguardando_material', label: 'Aguardando Material', cor: '#f97316' },
    { key: 'em_producao', label: 'Em Produção', cor: '#8b5cf6' },
    { key: 'para_embalar', label: 'Para Embalar', cor: '#06b6d4' },
    { key: 'pronto_entrega', label: 'Pronto', cor: '#10b981' },
    { key: 'entregue', label: 'Entregue', cor: '#22c55e' }
  ];

  const pedidosPorColuna = colunasKanban.reduce((acc, coluna) => {
    acc[coluna.key] = pedidos.filter(p => p.status_producao === coluna.key);
    return acc;
  }, {});

  const getClienteNome = (cliente) => {
    if (!cliente) return 'Cliente';
    return `${cliente.nome || ''} ${cliente.sobrenome || ''}`.trim() || 'Cliente';
  };

  const renderCardPedido = (p, isKanban = false) => (
    <div 
      key={p.id} 
      className="card fade-in" 
      style={{ cursor: 'pointer', transition: 'transform 0.2s', marginBottom: isKanban ? '0.75rem' : '0' }}
      onClick={() => setPedidoDetalhe(p)}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ marginBottom: '0.25rem' }}>#{p.numero_pedido}</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            {getClienteNome(p.cliente)}
          </p>
        </div>
        {!isKanban && <ChevronRight size={20} style={{ color: 'var(--text-secondary)' }} />}
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
        {getStatusBadge(p.status_geral, 'geral')}
        {getStatusBadge(p.status_producao, 'producao')}
        {getStatusBadge(p.status_financeiro, 'financeiro')}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '1rem', borderTop: '1px solid var(--glass-border)' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          {new Date(p.criado_em).toLocaleDateString('pt-BR')}
        </span>
        <span style={{ fontWeight: 'bold', color: 'var(--accent-primary)' }}>
          R$ {parseFloat(p.valor_total || 0).toFixed(2)}
        </span>
      </div>
    </div>
  );

  return (
    <div className="pedidos-page fade-in">
      <header className="page-header">
        <h1>Pedidos</h1>
        <div className="page-header-actions">
          <button 
            className={`btn ${visualizacao === 'kanban' ? 'btn-primary' : 'btn-glass'}`}
            onClick={() => setVisualizacao('kanban')}
            title="Kanban"
          >
            <LayoutGrid size={20} />
          </button>
          <button 
            className={`btn ${visualizacao === 'lista' ? 'btn-primary' : 'btn-glass'}`}
            onClick={() => setVisualizacao('lista')}
            title="Lista"
          >
            <List size={20} />
          </button>
          <button className="btn btn-primary" onClick={() => setMostrarFormulario(true)} style={{ marginLeft: '0.5rem' }}>
            <Plus size={20} /> Novo Pedido
          </button>
        </div>
      </header>

      {visualizacao === 'kanban' ? (
        <div className="kanban-board">
          {colunasKanban.map(coluna => (
            <div key={coluna.key} className="kanban-column">
              <div className="kanban-header" style={{ background: coluna.cor }}>
                <span className="kanban-title">{coluna.label}</span>
                <span className="kanban-count">{pedidosPorColuna[coluna.key]?.length || 0}</span>
              </div>
              <div className="kanban-body">
                {pedidosPorColuna[coluna.key]?.length > 0 ? (
                  pedidosPorColuna[coluna.key].map(p => renderCardPedido(p, true))
                ) : (
                  <p className="kanban-empty">Sem pedidos</p>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid-auto">
          {pedidos.length > 0 ? (
            pedidos.map(p => renderCardPedido(p))
          ) : (
            <div className="card" style={{ gridColumn: '1/-1', textAlign: 'center', padding: '3rem' }}>
              <p style={{ color: 'var(--text-secondary)' }}>Nenhum pedido registrado ainda.</p>
            </div>
          )}
        </div>
      )}

      <style>{`
        .kanban-board {
          display: flex;
          gap: 1rem;
          overflow-x: auto;
          padding-bottom: 1rem;
          -webkit-overflow-scrolling: touch;
        }
        
        .kanban-column {
          min-width: 260px;
          flex: 0 0 260px;
          max-width: 320px;
        }
        
        .kanban-header {
          color: white;
          padding: 1rem 1.25rem;
          border-radius: 10px 10px 0 0;
          font-weight: 600;
          font-size: 0.95rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
          box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        
        .kanban-count {
          background: rgba(255,255,255,0.25);
          padding: 0.25rem 0.75rem;
          border-radius: 20px;
          font-size: 0.85rem;
          font-weight: 600;
        }
        
        .kanban-body {
          background: var(--bg-secondary);
          padding: 1rem;
          border-radius: 0 0 10px 10px;
          min-height: 250px;
          max-height: calc(100vh - 340px);
          overflow-y: auto;
          border: 1px solid var(--glass-border);
          border-top: none;
        }
        
        .kanban-empty {
          color: var(--text-secondary);
          text-align: center;
          font-size: 0.9rem;
          padding: 2rem 0;
        }
        
        @media (min-width: 1400px) {
          .kanban-column {
            min-width: 300px;
            flex: 0 0 300px;
          }
        }
        
        @media (max-width: 1023px) {
          .kanban-column {
            min-width: 240px;
            flex: 0 0 240px;
          }
        }
        
        @media (max-width: 767px) {
          .kanban-column {
            min-width: 180px;
            flex: 0 0 180px;
            max-width: 200px;
          }
          
          .kanban-body {
            max-height: 60vh;
          }
        }
        
        @media (min-width: 768px) and (max-width: 1023px) {
          .kanban-column {
            min-width: 200px;
            flex: 0 0 200px;
          }
        }
      `}</style>
    </div>
  );
};

export default Pedidos;
