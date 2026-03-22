import React, { useState, useEffect } from 'react';
import api from '../api/config';
import { Calculator, RefreshCw, Plus, Trash2 } from 'lucide-react';

const Calculadora = () => {
  const [materiais, setMateriais] = useState({ molduras: [], vidros: [], fundos: [] });
  const [obra, setObra] = useState({ largura: 50, altura: 40 });
  const [paspatour, setPaspatour] = useState({ ativo: false, tamanho: 5 });
  const [molduras, setMolduras] = useState([]);
  const [vidroTipo, setVidroTipo] = useState('incolor');
  const [fundoId, setFundoId] = useState('');
  const [quantidade, setQuantidade] = useState(1);
  const [resultado, setResultado] = useState(null);
  const [carregando, setCarregando] = useState(false);

  useEffect(() => {
    const carregarMateriais = async () => {
      try {
        const [m, v, f] = await Promise.all([
          api.get('/estoque/molduras'),
          api.get('/estoque/vidros'),
          api.get('/estoque/fundos')
        ]);
        setMateriais({ molduras: m.data, vidros: v.data, fundos: f.data });
      } catch (erro) {
        console.error('Erro ao carregar materiais:', erro);
      }
    };
    carregarMateriais();
  }, []);

  const adicionarMoldura = () => {
    setMolduras([...molduras, { moldura_id: '', ordem: molduras.length }]);
  };

  const removerMoldura = (index) => {
    setMolduras(molduras.filter((_, i) => i !== index).map((m, i) => ({ ...m, ordem: i })));
  };

  const atualizarMoldura = (index, molduraId) => {
    const novas = [...molduras];
    novas[index].moldura_id = molduraId;
    setMolduras(novas);
  };

  const calcular = async () => {
    if (!obra.largura || !obra.altura) {
      return alert('Informe largura e altura da obra.');
    }
    setCarregando(true);
    try {
      const payload = {
        obra_largura: parseFloat(obra.largura),
        obra_altura: parseFloat(obra.altura),
        molduras: molduras.filter(m => m.moldura_id).map(m => ({ moldura_id: parseInt(m.moldura_id), ordem: m.ordem })),
        paspatour: paspatour.ativo,
        tamanho_paspatour: paspatour.ativo ? parseFloat(paspatour.tamanho) : 0,
        vidro_tipo: vidroTipo,
        fundo_id: fundoId ? parseInt(fundoId) : null,
        quantidade: parseInt(quantidade)
      };
      const resposta = await api.post('/calculadora/quadro', payload);
      setResultado(resposta.data);
    } catch (erro) {
      alert('Erro no calculo: ' + (erro.response?.data?.detail || erro.message));
    }
    setCarregando(false);
  };

  return (
    <div className="calculadora-page fade-in">
      <header style={{ marginBottom: '2rem' }}>
        <h1>Calculadora de Quadros</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Calcule precos com paspatour, multiplas molduras e propagacao de dimensoes.</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '2rem' }}>
        {/* Formulario */}
        <div>
          <div className="card" style={{ marginBottom: '1rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>Obra</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Largura (cm)</label>
                <input type="number" className="input-control" value={obra.largura} onChange={(e) => setObra({ ...obra, largura: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Altura (cm)</label>
                <input type="number" className="input-control" value={obra.altura} onChange={(e) => setObra({ ...obra, altura: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Quantidade</label>
                <input type="number" className="input-control" value={quantidade} onChange={(e) => setQuantidade(e.target.value)} min="1" />
              </div>
            </div>
          </div>

          <div className="card" style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3>Paspatour</h3>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                <input type="checkbox" checked={paspatour.ativo} onChange={(e) => setPaspatour({ ...paspatour, ativo: e.target.checked })} />
                <span style={{ fontSize: '0.85rem' }}>Usar paspatour</span>
              </label>
            </div>
            {paspatour.ativo && (
              <div className="form-group">
                <label>Tamanho do paspatour (cm)</label>
                <input type="number" className="input-control" value={paspatour.tamanho} onChange={(e) => setPaspatour({ ...paspatour, tamanho: e.target.value })} />
              </div>
            )}
          </div>

          <div className="card" style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3>Molduras</h3>
              <button className="btn btn-glass" style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }} onClick={adicionarMoldura}>
                <Plus size={14} /> Adicionar
              </button>
            </div>
            {molduras.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {molduras.map((m, index) => (
                  <div key={index} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', minWidth: '20px' }}>{index + 1}.</span>
                    <select className="input-control" value={m.moldura_id} onChange={(e) => atualizarMoldura(index, e.target.value)} style={{ flex: 1 }}>
                      <option value="">Selecione...</option>
                      {materiais.molduras.map(mol => (
                        <option key={mol.id} value={mol.id}>{mol.codigo} - {mol.cor} (R$ {parseFloat(mol.preco_venda).toFixed(2)}/m)</option>
                      ))}
                    </select>
                    <button className="btn-icon" onClick={() => removerMoldura(index)}>
                      <Trash2 size={16} color="var(--danger)" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', textAlign: 'center', padding: '0.5rem' }}>Nenhuma moldura adicionada</p>
            )}
          </div>

          <div className="card" style={{ marginBottom: '1rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>Materiais</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>Tipo de Vidro</label>
                <select className="input-control" value={vidroTipo} onChange={(e) => setVidroTipo(e.target.value)}>
                  <option value="incolor">Incolor</option>
                  <option value="antireflexo">Antireflexo</option>
                  <option value="espelho">Espelho</option>
                  <option value="outro">Outro</option>
                </select>
              </div>
              <div className="form-group">
                <label>Fundo</label>
                <select className="input-control" value={fundoId} onChange={(e) => setFundoId(e.target.value)}>
                  <option value="">Nenhum</option>
                  {materiais.fundos.map(f => <option key={f.id} value={f.id}>{f.tipo}</option>)}
                </select>
              </div>
            </div>
          </div>

          <button className="btn btn-primary" style={{ width: '100%' }} onClick={calcular} disabled={carregando}>
            <Calculator size={20} /> {carregando ? 'Calculando...' : 'Calcular'}
          </button>
        </div>

        {/* Resultado */}
        <div className="card" style={{ minHeight: '400px' }}>
          {resultado ? (
            <div className="fade-in">
              <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Total Estimado</p>
                <h1 style={{ fontSize: '2.5rem', color: 'var(--accent-primary)' }}>
                  R$ {parseFloat(resultado.total_sugerido).toFixed(2)}
                </h1>
                {quantidade > 1 && (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    R$ {(parseFloat(resultado.total_sugerido) / quantidade).toFixed(2)} por unidade
                  </p>
                )}
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <h4 style={{ marginBottom: '0.75rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>DIMENSOES</h4>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Obra:</span>
                    <span>{obra.largura} x {obra.altura} cm</span>
                  </div>
                  {paspatour.ativo && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Vidro:</span>
                      <span>{resultado.dimensoes.vidro.largura} x {resultado.dimensoes.vidro.altura} cm</span>
                    </div>
                  )}
                  {resultado.dimensoes.molduras.map((m, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Moldura {i + 1}:</span>
                      <span>{m.largura} x {m.altura} cm</span>
                    </div>
                  ))}
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold', paddingTop: '0.5rem', borderTop: '1px solid var(--glass-border)' }}>
                    <span>Quadro Final:</span>
                    <span style={{ color: 'var(--accent-primary)' }}>{resultado.dimensoes.quadro_final.largura} x {resultado.dimensoes.quadro_final.altura} cm</span>
                  </div>
                </div>
              </div>

              <div>
                <h4 style={{ marginBottom: '0.75rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>CUSTOS</h4>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px' }}>
                  {resultado.custos.map((c, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>{c.nome} <span style={{ fontSize: '0.75rem' }}>({parseFloat(c.medida).toFixed(2)} {c.unidade})</span></span>
                      <span style={{ color: 'var(--accent-primary)' }}>R$ {parseFloat(c.subtotal).toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <button className="btn btn-glass" style={{ marginTop: '1.5rem', width: '100%' }} onClick={() => setResultado(null)}>
                <RefreshCw size={18} /> Nova Simulacao
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
              <Calculator size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
              <p>Preencha os dados e clique em calcular.</p>
            </div>
          )}
        </div>
      </div>

      <style>{`
        .btn-icon { background: none; border: none; cursor: pointer; color: var(--text-secondary); transition: color 0.2s; padding: 0.25rem; }
        .btn-icon:hover { color: var(--text-primary); }
      `}</style>
    </div>
  );
};

export default Calculadora;
