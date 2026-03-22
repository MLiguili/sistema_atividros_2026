import React, { useState, useEffect, useCallback } from 'react';
import api from '../api/config';
import { Plus, Search, Edit2, Trash2, X, Save, AlertTriangle } from 'lucide-react';

const Estoque = () => {
  const [abaAtiva, setAbaAtiva] = useState('molduras');
  const [itens, setItens] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [termoBusca, setTermoBusca] = useState('');
  const [modalAberto, setModalAberto] = useState(null);
  const [itemEditando, setItemEditando] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [erro, setErro] = useState('');

  const carregarDados = useCallback(async () => {
    setCarregando(true);
    try {
      const resposta = await api.get(`/estoque/${abaAtiva}`);
      setItens(resposta.data);
    } catch (err) {
      console.error(`Erro ao carregar ${abaAtiva}:`, err);
    }
    setCarregando(false);
  }, [abaAtiva]);

  useEffect(() => {
    carregarDados();
  }, [carregarDados]);

  const itensFiltrados = itens.filter(item => 
    Object.values(item).some(val => 
      String(val).toLowerCase().includes(termoBusca.toLowerCase())
    )
  );

  const abrirModalCriar = () => {
    setItemEditando(null);
    setErro('');
    setModalAberto('criar');
  };

  const abrirModalEditar = (item) => {
    setItemEditando(item);
    setErro('');
    setModalAberto('editar');
  };

  const fecharModal = () => {
    setModalAberto(null);
    setItemEditando(null);
    setErro('');
  };

  const handleSalvar = async (dados) => {
    try {
      if (itemEditando) {
        await api.put(`/estoque/${abaAtiva}/${itemEditando.id}`, dados);
      } else {
        await api.post(`/estoque/${abaAtiva}`, dados);
      }
      carregarDados();
      fecharModal();
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao salvar');
    }
  };

  const handleDeletar = async (id) => {
    try {
      await api.delete(`/estoque/${abaAtiva}/${id}`);
      carregarDados();
      setConfirmDelete(null);
    } catch (err) {
      alert('Erro ao deletar: ' + (err.response?.data?.detail || err.message));
    }
  };

  const colunas = getColunas(abaAtiva);

  return (
    <div className="estoque-page fade-in">
      <header className="page-header">
        <div>
          <h1>Gestão de Estoque</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Gerencie molduras, vidros, fundos e suplementos.</p>
        </div>
        <button className="btn btn-primary" onClick={abrirModalCriar}>
          <Plus size={20} /> <span className="hide-mobile">Novo Item</span>
        </button>
      </header>

      <div className="tabs">
        <TabButton ativa={abaAtiva === 'molduras'} onClick={() => setAbaAtiva('molduras')} texto="Molduras" />
        <TabButton ativa={abaAtiva === 'vidros'} onClick={() => setAbaAtiva('vidros')} texto="Vidros" />
        <TabButton ativa={abaAtiva === 'fundos'} onClick={() => setAbaAtiva('fundos')} texto="Fundos" />
        <TabButton ativa={abaAtiva === 'suplementos'} onClick={() => setAbaAtiva('suplementos')} texto="Suplementos" />
      </div>

      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem' }}>
        <div style={{ position: 'relative' }}>
          <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)', zIndex: 1 }} />
          <input 
            type="text" 
            placeholder={`Buscar em ${abaAtiva}...`} 
            className="input-control" 
            style={{ paddingLeft: '40px' }}
            value={termoBusca}
            onChange={(e) => setTermoBusca(e.target.value)}
          />
        </div>
      </div>

      <div className="card table-container" style={{ padding: 0 }}>
        {carregando ? (
          <div className="loading">Carregando dados...</div>
        ) : itensFiltrados.length === 0 ? (
          <div className="loading" style={{ color: 'var(--text-secondary)' }}>
            Nenhum item encontrado
          </div>
        ) : (
          <table>
            <thead style={{ backgroundColor: 'rgba(255,255,255,0.03)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <tr>
                {colunas.map(col => <th key={col.key} style={{ padding: '1rem' }}>{col.label}</th>)}
                <th style={{ padding: '1rem', textAlign: 'right' }}>Ações</th>
              </tr>
            </thead>
            <tbody>
              {itensFiltrados.map((item) => (
                <tr key={item.id} style={{ borderTop: '1px solid var(--glass-border)' }} className="table-row-hover">
                  {colunas.map(col => (
                    <td key={col.key} style={{ padding: '1rem' }}>
                      {col.render ? col.render(item[col.key], item) : item[col.key]}
                    </td>
                  ))}
                  <td style={{ padding: '1rem', textAlign: 'right' }}>
                    <button className="btn-icon" onClick={() => abrirModalEditar(item)} title="Editar">
                      <Edit2 size={16} />
                    </button>
                    <button className="btn-icon" onClick={() => setConfirmDelete(item)} title="Excluir" style={{ marginLeft: '0.5rem' }}>
                      <Trash2 size={16} color="var(--danger)" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {modalAberto && (
        <ModalFormulario
          tipo={abaAtiva}
          item={itemEditando}
          onSalvar={handleSalvar}
          onFechar={fecharModal}
          erro={erro}
        />
      )}

      {confirmDelete && (
        <ModalConfirmacao
          item={confirmDelete}
          onConfirmar={() => handleDeletar(confirmDelete.id)}
          onCancelar={() => setConfirmDelete(null)}
        />
      )}

      <style>{`
        .tab-btn {
          padding: 0.75rem 1rem;
          cursor: pointer;
          color: var(--text-secondary);
          border-bottom: 2px solid transparent;
          transition: all 0.2s;
          background: none;
          border-top: none;
          border-left: none;
          border-right: none;
          font-weight: 500;
        }
        .tab-btn:hover { color: var(--text-primary); }
        .tab-btn.active { color: var(--accent-primary); border-bottom-color: var(--accent-primary); }
        .table-row-hover:hover { background-color: rgba(255,255,255,0.02); }
        .btn-icon { background: none; border: none; cursor: pointer; color: var(--text-secondary); transition: color 0.2s; padding: 0.25rem; border-radius: 4px; }
        .btn-icon:hover { color: var(--text-primary); background: rgba(255,255,255,0.05); }
        .text-danger { color: var(--danger); }
        .text-warning { color: #f59e0b; }
        .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000; }
        .modal-content { background: var(--card-bg); border: 1px solid var(--glass-border); border-radius: 12px; padding: 2rem; width: 100%; max-width: 500px; max-height: 90vh; overflow-y: auto; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
        .modal-footer { display: flex; gap: 1rem; justify-content: flex-end; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--glass-border); }
        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .form-group { margin-bottom: 1rem; }
        .form-group.full-width { grid-column: span 2; }
        label { display: block; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.5rem; }
        .input-control { width: 100%; }
      `}</style>
    </div>
  );
};

function getColunas(tipo) {
  switch (tipo) {
    case 'molduras':
      return [
        { key: 'codigo', label: 'Código' },
        { key: 'cor', label: 'Cor' },
        { key: 'quantidade', label: 'Qtd', render: (v) => <span className={v < 5 ? 'text-danger' : ''}>{v}</span> },
        { key: 'preco_venda', label: 'Preço Venda', render: (v) => `R$ ${parseFloat(v).toFixed(2)}` },
        { key: 'tamanho_barra', label: 'Tamanho Barra', render: (v) => `${v}m` },
        { key: 'largura_barra', label: 'Largura Barra', render: (v) => `${v}cm` },
      ];
    case 'vidros':
      return [
        { key: 'tipo', label: 'Tipo' },
        { key: 'espessura', label: 'Espessura', render: (v) => `${v}mm` },
        { key: 'quantidade', label: 'Qtd', render: (v) => <span className={v < 5 ? 'text-danger' : ''}>{v}</span> },
        { key: 'largura_chapa', label: 'Largura', render: (v) => `${v}cm` },
        { key: 'altura_chapa', label: 'Altura', render: (v) => `${v}cm` },
        { key: 'cor', label: 'Cor' },
      ];
    case 'fundos':
      return [
        { key: 'tipo', label: 'Tipo' },
        { key: 'espessura', label: 'Espessura', render: (v) => `${v}mm` },
        { key: 'quantidade', label: 'Qtd', render: (v) => <span className={v < 5 ? 'text-danger' : ''}>{v}</span> },
        { key: 'largura', label: 'Largura', render: (v) => `${v}cm` },
        { key: 'altura', label: 'Altura', render: (v) => `${v}cm` },
        { key: 'cor', label: 'Cor' },
      ];
    case 'suplementos':
      return [
        { key: 'nome', label: 'Nome' },
        { key: 'quantidade', label: 'Qtd', render: (v) => <span className={v < 5 ? 'text-danger' : ''}>{v}</span> },
        { key: 'unidade', label: 'Unidade' },
      ];
    default:
      return [];
  }
}

function getFormVazio(tipo) {
  switch (tipo) {
    case 'molduras':
      return { codigo: '', quantidade: 0, preco_venda: '', preco_custo: '', cor: '', tamanho_barra: '', largura_barra: '', marca: '' };
    case 'vidros':
      return { espessura: '', tipo: 'incolor', quantidade: 0, largura_chapa: '', altura_chapa: '', cor: '' };
    case 'fundos':
      return { tipo: '', espessura: '', quantidade: 0, largura: '', altura: '', cor: '' };
    case 'suplementos':
      return { nome: '', quantidade: 0, unidade: '' };
    default:
      return {};
  }
}

function ModalFormulario({ tipo, item, onSalvar, onFechar, erro }) {
  const [dados, setDados] = useState(item ? { ...item } : getFormVazio(tipo));

  const handleSubmit = (e) => {
    e.preventDefault();
    const dadosFormatados = { ...dados };
    
    if (tipo === 'molduras') {
      dadosFormatados.preco_venda = parseFloat(dadosFormatados.preco_venda);
      dadosFormatados.preco_custo = parseFloat(dadosFormatados.preco_custo);
      dadosFormatados.tamanho_barra = parseFloat(dadosFormatados.tamanho_barra);
      dadosFormatados.largura_barra = parseFloat(dadosFormatados.largura_barra);
      dadosFormatados.quantidade = parseInt(dadosFormatados.quantidade);
    } else if (tipo === 'vidros') {
      dadosFormatados.espessura = parseFloat(dadosFormatados.espessura);
      dadosFormatados.largura_chapa = parseFloat(dadosFormatados.largura_chapa);
      dadosFormatados.altura_chapa = parseFloat(dadosFormatados.altura_chapa);
      dadosFormatados.quantidade = parseInt(dadosFormatados.quantidade);
    } else if (tipo === 'fundos') {
      dadosFormatados.espessura = parseFloat(dadosFormatados.espessura);
      dadosFormatados.largura = parseFloat(dadosFormatados.largura);
      dadosFormatados.altura = parseFloat(dadosFormatados.altura);
      dadosFormatados.quantidade = parseInt(dadosFormatados.quantidade);
    } else if (tipo === 'suplementos') {
      dadosFormatados.quantidade = parseInt(dadosFormatados.quantidade);
    }

    onSalvar(dadosFormatados);
  };

  const setCampo = (campo, valor) => {
    setDados({ ...dados, [campo]: valor });
  };

  const titulo = item ? `Editar ${getNomeTipo(tipo)}` : `Nova ${getNomeTipo(tipo)}`;

  return (
    <div className="modal-overlay" onClick={onFechar}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{titulo}</h2>
          <button className="btn-icon" onClick={onFechar}><X size={20} /></button>
        </div>

        {erro && (
          <div style={{ background: 'rgba(239,68,68,0.1)', color: 'var(--danger)', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertTriangle size={16} /> {erro}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {tipo === 'molduras' && (
            <div className="form-grid">
              <div className="form-group">
                <label>Código *</label>
                <input type="text" className="input-control" value={dados.codigo} onChange={e => setCampo('codigo', e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Cor *</label>
                <input type="text" className="input-control" value={dados.cor} onChange={e => setCampo('cor', e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Quantidade *</label>
                <input type="number" className="input-control" value={dados.quantidade} onChange={e => setCampo('quantidade', e.target.value)} min="0" required />
              </div>
              <div className="form-group">
                <label>Marca</label>
                <input type="text" className="input-control" value={dados.marca || ''} onChange={e => setCampo('marca', e.target.value)} />
              </div>
              <div className="form-group">
                <label>Preço de Venda (R$) *</label>
                <input type="number" className="input-control" value={dados.preco_venda} onChange={e => setCampo('preco_venda', e.target.value)} step="0.01" min="0" required />
              </div>
              <div className="form-group">
                <label>Preço de Custo (R$) *</label>
                <input type="number" className="input-control" value={dados.preco_custo} onChange={e => setCampo('preco_custo', e.target.value)} step="0.01" min="0" required />
              </div>
              <div className="form-group">
                <label>Tamanho da Barra (m) *</label>
                <input type="number" className="input-control" value={dados.tamanho_barra} onChange={e => setCampo('tamanho_barra', e.target.value)} step="0.01" min="0" required />
              </div>
              <div className="form-group">
                <label>Largura da Barra (cm) *</label>
                <input type="number" className="input-control" value={dados.largura_barra} onChange={e => setCampo('largura_barra', e.target.value)} step="0.01" min="0" required />
              </div>
            </div>
          )}

          {tipo === 'vidros' && (
            <div className="form-grid">
              <div className="form-group">
                <label>Tipo *</label>
                <select className="input-control" value={dados.tipo} onChange={e => setCampo('tipo', e.target.value)} required>
                  <option value="incolor">Incolor</option>
                  <option value="antireflexo">Antireflexo</option>
                  <option value="espelho">Espelho</option>
                  <option value="outro">Outro</option>
                </select>
              </div>
              <div className="form-group">
                <label>Espessura (mm) *</label>
                <input type="number" className="input-control" value={dados.espessura} onChange={e => setCampo('espessura', e.target.value)} step="0.1" min="0" required />
              </div>
              <div className="form-group">
                <label>Quantidade (chapas) *</label>
                <input type="number" className="input-control" value={dados.quantidade} onChange={e => setCampo('quantidade', e.target.value)} min="0" required />
              </div>
              <div className="form-group">
                <label>Cor</label>
                <input type="text" className="input-control" value={dados.cor || ''} onChange={e => setCampo('cor', e.target.value)} />
              </div>
              <div className="form-group">
                <label>Largura da Chapa (cm) *</label>
                <input type="number" className="input-control" value={dados.largura_chapa} onChange={e => setCampo('largura_chapa', e.target.value)} step="0.1" min="0" required />
              </div>
              <div className="form-group">
                <label>Altura da Chapa (cm) *</label>
                <input type="number" className="input-control" value={dados.altura_chapa} onChange={e => setCampo('altura_chapa', e.target.value)} step="0.1" min="0" required />
              </div>
            </div>
          )}

          {tipo === 'fundos' && (
            <div className="form-grid">
              <div className="form-group">
                <label>Tipo *</label>
                <input type="text" className="input-control" value={dados.tipo} onChange={e => setCampo('tipo', e.target.value)} placeholder="Ex: MDF, Compensado" required />
              </div>
              <div className="form-group">
                <label>Espessura (mm) *</label>
                <input type="number" className="input-control" value={dados.espessura} onChange={e => setCampo('espessura', e.target.value)} step="0.1" min="0" required />
              </div>
              <div className="form-group">
                <label>Quantidade *</label>
                <input type="number" className="input-control" value={dados.quantidade} onChange={e => setCampo('quantidade', e.target.value)} min="0" required />
              </div>
              <div className="form-group">
                <label>Cor</label>
                <input type="text" className="input-control" value={dados.cor || ''} onChange={e => setCampo('cor', e.target.value)} />
              </div>
              <div className="form-group">
                <label>Largura (cm) *</label>
                <input type="number" className="input-control" value={dados.largura} onChange={e => setCampo('largura', e.target.value)} step="0.1" min="0" required />
              </div>
              <div className="form-group">
                <label>Altura (cm) *</label>
                <input type="number" className="input-control" value={dados.altura} onChange={e => setCampo('altura', e.target.value)} step="0.1" min="0" required />
              </div>
            </div>
          )}

          {tipo === 'suplementos' && (
            <div>
              <div className="form-group">
                <label>Nome *</label>
                <input type="text" className="input-control" value={dados.nome} onChange={e => setCampo('nome', e.target.value)} placeholder="Ex: Cola, Grampos, Fita" required />
              </div>
              <div className="form-grid">
                <div className="form-group">
                  <label>Quantidade *</label>
                  <input type="number" className="input-control" value={dados.quantidade} onChange={e => setCampo('quantidade', e.target.value)} min="0" required />
                </div>
                <div className="form-group">
                  <label>Unidade</label>
                  <input type="text" className="input-control" value={dados.unidade || ''} onChange={e => setCampo('unidade', e.target.value)} placeholder="Ex: ml, kg, un" />
                </div>
              </div>
            </div>
          )}

          <div className="modal-footer">
            <button type="button" className="btn btn-glass" onClick={onFechar}>Cancelar</button>
            <button type="submit" className="btn btn-primary"><Save size={18} /> Salvar</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ModalConfirmacao({ item, onConfirmar, onCancelar }) {
  const nomeItem = item.codigo || item.nome || item.tipo || `Item #${item.id}`;

  return (
    <div className="modal-overlay" onClick={onCancelar}>
      <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '400px' }}>
        <div style={{ textAlign: 'center' }}>
          <AlertTriangle size={48} color="var(--danger)" style={{ marginBottom: '1rem' }} />
          <h3 style={{ marginBottom: '1rem' }}>Confirmar Exclusão</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
            Tem certeza que deseja excluir <strong>{nomeItem}</strong>? Esta ação não pode ser desfeita.
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

function getNomeTipo(tipo) {
  const nomes = {
    molduras: 'Moldura',
    vidros: 'Vidro',
    fundos: 'Fundo',
    suplementos: 'Suplemento'
  };
  return nomes[tipo] || tipo;
}

function TabButton({ ativa, onClick, texto }) {
  return (
    <button className={`tab-btn ${ativa ? 'active' : ''}`} onClick={onClick}>
      {texto}
    </button>
  );
}

export default Estoque;
