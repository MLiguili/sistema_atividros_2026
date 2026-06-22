import React, { useState, useEffect, useCallback } from 'react';
import api from '../api/config';
import { FileText, Download, Printer, Search, Tag, FileSpreadsheet, File as FilePdf, AlertCircle, CheckCircle } from 'lucide-react';

const EtiquetasRelatorios = () => {
  const [aba, setAba] = useState('etiquetas');
  const [pedidos, setPedidos] = useState([]);
  const [busca, setBusca] = useState('');
  const [gerando, setGerando] = useState(null);

  const carregarPedidos = useCallback(async () => {
    try {
      const resp = await api.get('/pedidos/');
      setPedidos(resp.data);
    } catch (erro) {
      console.error('Erro ao carregar pedidos:', erro);
    }
  }, []);

  useEffect(() => {
    if (aba === 'etiquetas') carregarPedidos();
  }, [aba, carregarPedidos]);

  const filtrarPedidos = (p) => {
    if (!busca) return true;
    const termo = busca.toLowerCase();
    return (
      p.numero_pedido?.toLowerCase().includes(termo) ||
      p.cliente?.nome?.toLowerCase().includes(termo) ||
      p.cliente?.sobrenome?.toLowerCase().includes(termo)
    );
  };

  const handleDownloadEtiqueta = async (pedidoId) => {
    setGerando(pedidoId);
    try {
      const resp = await api.get(`/etiquetas/pedido/${pedidoId}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `etiqueta_${pedidoId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (erro) {
      console.error('Erro ao gerar etiqueta:', erro);
    } finally {
      setGerando(null);
    }
  };

  const handleDownloadReport = async (tipo, formato) => {
    setGerando(tipo + formato);
    try {
      const resp = await api.get(`/relatorios/${tipo}/${formato}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${tipo}.${formato}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (erro) {
      console.error('Erro ao gerar relatório:', erro);
    } finally {
      setGerando(null);
    }
  };

  return (
    <div className="fade-in">
      <header className="page-header">
        <h1>Etiquetas e Relatórios</h1>
      </header>

      <div className="tabs">
        <button className={`tab ${aba === 'etiquetas' ? 'active' : ''}`} onClick={() => setAba('etiquetas')}>
          <Tag size={16} /> Etiquetas
        </button>
        <button className={`tab ${aba === 'relatorios' ? 'active' : ''}`} onClick={() => setAba('relatorios')}>
          <FileText size={16} /> Relatórios
        </button>
      </div>

      {aba === 'etiquetas' && (
        <>
          <div style={{ marginBottom: '1rem' }}>
            <div className="input-group" style={{ maxWidth: 400 }}>
              <Search size={16} />
              <input
                className="input-control"
                placeholder="Buscar por pedido ou cliente..."
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
              />
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {pedidos.filter(filtrarPedidos).map((p) => (
              <div key={p.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem' }}>
                <div>
                  <p style={{ fontWeight: 500, fontSize: '0.9rem' }}>
                    #{p.numero_pedido} — {p.cliente?.nome} {p.cliente?.sobrenome}
                  </p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    R$ {parseFloat(p.valor_total || 0).toFixed(2)} | {p.status_producao?.replace('_', ' ')}
                  </p>
                </div>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => handleDownloadEtiqueta(p.id)}
                  disabled={gerando === p.id}
                  style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
                >
                  {gerando === p.id ? <AlertCircle size={14} /> : <Printer size={14} />}
                  {gerando === p.id ? 'Gerando...' : 'Etiqueta'}
                </button>
              </div>
            ))}
            {pedidos.filter(filtrarPedidos).length === 0 && (
              <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem' }}>Nenhum pedido encontrado</p>
            )}
          </div>
        </>
      )}

      {aba === 'relatorios' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <FileText size={24} color="var(--accent-primary)" />
              <div>
                <p style={{ fontWeight: 500 }}>Relatório de Pedidos</p>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Exportar lista completa de pedidos</p>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button className="btn btn-secondary btn-sm" onClick={() => handleDownloadReport('pedidos', 'csv')} disabled={gerando === 'pedidoscsv'} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <FileSpreadsheet size={14} /> CSV
              </button>
              <button className="btn btn-primary btn-sm" onClick={() => handleDownloadReport('pedidos', 'pdf')} disabled={gerando === 'pedidospdf'} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <FilePdf size={14} /> PDF
              </button>
            </div>
          </div>

          <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Users size={24} color="#8b5cf6" />
              <div>
                <p style={{ fontWeight: 500 }}>Relatório de Clientes</p>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Exportar cadastro de clientes</p>
              </div>
            </div>
            <button className="btn btn-primary btn-sm" onClick={() => handleDownloadReport('clientes', 'pdf')} disabled={gerando === 'clientespdf'} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <FilePdf size={14} /> PDF
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default EtiquetasRelatorios;
