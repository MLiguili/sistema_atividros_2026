import React, { useState, useEffect } from 'react';
import api from '../api/config';
import { Package, Users, ShoppingCart, TrendingUp, AlertCircle, CheckCircle, Calendar } from 'lucide-react';

const Dashboard = () => {
  const [resumo, setResumo] = useState({ molduras: 0, vidros: 0, fundos: 0, pedidos: 0, clientes: 0, receita: 0 });
  const [pedidosHoje, setPedidosHoje] = useState([]);
  const [alertasEstoque, setAlertasEstoque] = useState([]);

  useEffect(() => {
    const carregarDados = async () => {
      try {
        const [m, v, f, p, c] = await Promise.all([
          api.get('/estoque/molduras'),
          api.get('/estoque/vidros'),
          api.get('/estoque/fundos'),
          api.get('/pedidos/'),
          api.get('/clientes/')
        ]);
        
        const totalReceita = p.data.reduce((acc, curr) => acc + parseFloat(curr.valor_total || 0), 0);
        
        const hoje = new Date().toISOString().split('T')[0];
        const pedidosDeHoje = p.data.filter(pedido => 
          pedido.criado_em && pedido.criado_em.startsWith(hoje)
        );
        const pedidosOrd = [...pedidosDeHoje].sort((a, b) => new Date(b.criado_em) - new Date(a.criado_em));
        
        setResumo({
          molduras: m.data.length,
          vidros: v.data.length,
          fundos: f.data.length,
          pedidos: p.data.length,
          clientes: c.data.length,
          receita: totalReceita
        });
        setPedidosHoje(pedidosOrd);
        
        const alertas = [
          ...m.data.filter(item => item.quantidade < 5).map(item => ({ ...item, tipo_item: 'moldura' })),
          ...v.data.filter(item => item.quantidade < 3).map(item => ({ ...item, tipo_item: 'vidro' })),
          ...f.data.filter(item => item.quantidade < 3).map(item => ({ ...item, tipo_item: 'fundo' }))
        ];
        setAlertasEstoque(alertas);
      } catch (erro) {
        console.error('Erro ao carregar dados:', erro);
      }
    };
    carregarDados();
  }, []);

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

  const getNomeItem = (item) => {
    if (item.tipo_item === 'moldura') return item.codigo || 'Moldura';
    if (item.tipo_item === 'vidro') return `${item.tipo} ${item.espessura}mm`;
    if (item.tipo_item === 'fundo') return `${item.tipo} ${item.espessura}mm`;
    return 'Item';
  };

  return (
    <div className="dashboard-wrapper">
      <header className="page-header">
        <div>
          <h1>Painel Geral</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Bem-vindo de volta! Aqui está o resumo da Atividros hoje.</p>
        </div>
      </header>

      <div className="stats-grid" style={{ marginBottom: 'var(--spacing-lg)' }}>
        <StatCard icone={<Package size={24} color="#10b981" />} rotulo="Molduras" valor={resumo.molduras} cor="#10b981" />
        <StatCard icone={<Package size={24} color="#3b82f6" />} rotulo="Vidros" valor={resumo.vidros} cor="#3b82f6" />
        <StatCard icone={<Package size={24} color="#f59e0b" />} rotulo="Fundos" valor={resumo.fundos} cor="#f59e0b" />
        <StatCard icone={<ShoppingCart size={24} color="#8b5cf6" />} rotulo="Pedidos" valor={resumo.pedidos} cor="#8b5cf6" />
        <StatCard icone={<Users size={24} color="#6366f1" />} rotulo="Clientes" valor={resumo.clientes} cor="#6366f1" />
        <StatCard icone={<TrendingUp size={24} color="#ec4899" />} rotulo="Receita" valor={`R$ ${resumo.receita.toFixed(2)}`} cor="#ec4899" />
      </div>

      <div className="grid-2">
        <div className="card">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Calendar size={18} /> Pedidos de Hoje
          </h3>
          {pedidosHoje.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {pedidosHoje.map(pedido => (
                <div key={pedido.id} style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center', 
                  padding: '0.75rem', 
                  background: 'rgba(255,255,255,0.02)', 
                  borderRadius: '8px' 
                }}>
                  <div>
                    <p style={{ fontWeight: 500 }}>#{pedido.numero_pedido}</p>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {pedido.cliente?.nome || 'Cliente'} {pedido.cliente?.sobrenome || ''}
                    </p>
                    <div style={{ display: 'flex', gap: '0.25rem', marginTop: '0.25rem' }}>
                      {getStatusBadge(pedido.status_geral, 'geral')}
                      {getStatusBadge(pedido.status_producao, 'producao')}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>
                      R$ {parseFloat(pedido.valor_total || 0).toFixed(2)}
                    </p>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      {new Date(pedido.criado_em).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', padding: '2rem', justifyContent: 'center' }}>
              <CheckCircle size={20} /> Nenhum pedido hoje
            </div>
          )}
        </div>

        <div className="card">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <AlertCircle size={18} color="#ef4444" /> Estoque Critico
          </h3>
          {alertasEstoque.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {alertasEstoque.map(item => (
                <div key={`${item.tipo_item}-${item.id}`} style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '0.75rem', 
                  padding: '0.75rem', 
                  background: 'rgba(239,68,68,0.1)', 
                  borderRadius: '8px', 
                  border: '1px solid rgba(239,68,68,0.2)' 
                }}>
                  <AlertCircle size={18} color="#ef4444" />
                  <div style={{ flex: 1 }}>
                    <p style={{ fontWeight: 500 }}>{getNomeItem(item)}</p>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                      {item.tipo_item}
                    </p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontWeight: 600, color: '#ef4444' }}>{item.quantidade} un</p>
                    <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Baixo</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', padding: '2rem', justifyContent: 'center' }}>
              <CheckCircle size={20} color="#10b981" /> Estoque OK
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ icone, rotulo, valor, cor }) => (
  <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '1rem' }}>
    <div style={{ 
      width: '40px', 
      height: '40px', 
      borderRadius: '10px', 
      backgroundColor: `rgba(${parseInt(cor.slice(1,3), 16)}, ${parseInt(cor.slice(3,5), 16)}, ${parseInt(cor.slice(5,7), 16)}, 0.1)`, 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      flexShrink: 0
    }}>
      {icone}
    </div>
    <div>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: '0.15rem' }}>{rotulo}</p>
      <p style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{valor}</p>
    </div>
  </div>
);

export default Dashboard;
