import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  CircleDollarSign,
  FileEdit,
  ShoppingCart,
  TrendingUp,
} from 'lucide-react';
import api from '../api/config';
import Card from '../components/ui/Card';
import StatCard from '../components/ui/StatCard';
import Callout from '../components/ui/Callout';
import EmptyState from '../components/ui/EmptyState';
import { formatarAreaM2, formatarMoeda } from '../utils/formatadores';

/**
 * Painel operacional exibindo KPIs financeiros confiáveis, prazos e alertas de ruptura de estoque.
 *
 * @returns {JSX.Element} Página Dashboard.
 */
const Dashboard = () => {
  const [resumo, setResumo] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');

  useEffect(() => {
    const carregar = async () => {
      try {
        const resp = await api.get('/dashboard/resumo');
        setResumo(resp.data);
      } catch (err) {
        setErro(err.response?.data?.detail || 'Não foi possível carregar o resumo operacional.');
      } finally {
        setCarregando(false);
      }
    };
    carregar();
  }, []);

  if (carregando) {
    return (
      <div className="at-state" role="status">
        Carregando painel operacional...
      </div>
    );
  }

  if (erro || !resumo) {
    return (
      <div>
        <header className="at-page-header">
          <h1>Painel Geral</h1>
        </header>
        <Callout variant="danger">{erro || 'Erro ao carregar dados.'}</Callout>
      </div>
    );
  }

  const { alertas_estoque: alertas } = resumo;
  const totalCriticos =
    (alertas?.molduras_criticas?.length || 0) +
    (alertas?.vidros_criticos?.length || 0) +
    (alertas?.fundos_criticos?.length || 0);

  return (
    <div>
      <header className="at-page-header">
        <div>
          <h1>Painel Geral</h1>
          <p className="at-page-header__subtitle">
            Resumo financeiro confirmado, prazos de entrega e alertas de estoque da loja.
          </p>
        </div>
        <div className="at-page-header__actions">
          <Link to="/calculadora" className="at-btn at-btn--secondary">
            Abrir Calculadora
          </Link>
          <Link to="/pedidos" className="at-btn at-btn--primary">
            Gerenciar Pedidos
          </Link>
        </div>
      </header>

      <div className="at-stats-grid">
        <StatCard
          icon={<TrendingUp size={20} aria-hidden="true" />}
          label="Receita Confirmada"
          value={formatarMoeda(resumo.receita_confirmada)}
          tone="brand"
        />
        <StatCard
          icon={<CircleDollarSign size={20} aria-hidden="true" />}
          label="Saldo a Receber"
          value={formatarMoeda(resumo.total_a_receber)}
          tone="warning"
        />
        <StatCard
          icon={<ShoppingCart size={20} aria-hidden="true" />}
          label="Pedidos Ativos"
          value={resumo.pedidos_ativos}
          tone="info"
        />
        <StatCard
          icon={<FileEdit size={20} aria-hidden="true" />}
          label="Orçamentos Abertos"
          value={resumo.orcamentos_abertos}
          tone="info"
        />
        <StatCard
          icon={<CalendarClock size={20} aria-hidden="true" />}
          label="Prazos Vencidos"
          value={resumo.pedidos_prazo_vencido}
          tone={resumo.pedidos_prazo_vencido > 0 ? 'danger' : 'brand'}
        />
        <StatCard
          icon={<CalendarClock size={20} aria-hidden="true" />}
          label="Vencendo Hoje"
          value={resumo.pedidos_vencendo_hoje}
          tone={resumo.pedidos_vencendo_hoje > 0 ? 'warning' : 'brand'}
        />
      </div>

      <div className="at-grid-2">
        <Card>
          <div className="at-card__header">
            <h2>Movimento e Prazos</h2>
            <span className="at-muted at-num">{resumo.pedidos_hoje} criados hoje</span>
          </div>

          {resumo.pedidos_prazo_vencido > 0 && (
            <Callout variant="danger">
              Há <strong className="at-num">{resumo.pedidos_prazo_vencido}</strong> pedido(s) confirmado(s) com prazo de entrega vencido.
            </Callout>
          )}
          {resumo.pedidos_vencendo_hoje > 0 && (
            <Callout variant="warning">
              <strong className="at-num">{resumo.pedidos_vencendo_hoje}</strong> pedido(s) vencem hoje na oficina.
            </Callout>
          )}
          {resumo.pedidos_prazo_vencido === 0 && resumo.pedidos_vencendo_hoje === 0 && (
            <EmptyState
              icon={<CheckCircle2 size={32} aria-hidden="true" />}
              title="Prazos sob controle"
              description="Nenhum pedido ativo está atrasado ou vencendo hoje."
            />
          )}
        </Card>

        <Card>
          <div className="at-card__header">
            <h2>Estoque Crítico e Rupturas</h2>
            <Link to="/estoque" className="at-btn at-btn--ghost at-btn--sm">
              Ver Estoque
            </Link>
          </div>

          {totalCriticos === 0 ? (
            <EmptyState
              icon={<CheckCircle2 size={32} aria-hidden="true" />}
              title="Estoque em dia"
              description="Nenhuma moldura, vidro ou fundo abaixo do mínimo configurado."
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-2)' }}>
              {alertas.molduras_criticas.map((m) => (
                <div
                  key={`m-${m.id}`}
                  className={`at-baixa-row ${m.quantidade < 0 ? 'at-baixa-row--ruptura' : ''}`.trim()}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--at-space-2)' }}>
                    <AlertTriangle size={16} aria-hidden="true" />
                    <div>
                      <strong>Moldura {m.codigo}</strong> <span className="at-muted">({m.cor})</span>
                      <p className="at-field__hint at-num">Mínimo: {m.estoque_minimo} barras</p>
                    </div>
                  </div>
                  <strong className="at-num">
                    {m.quantidade} {m.quantidade === 1 || m.quantidade === -1 ? 'barra' : 'barras'}
                  </strong>
                </div>
              ))}

              {alertas.vidros_criticos.map((v) => (
                <div
                  key={`v-${v.id}`}
                  className={`at-baixa-row ${Number(v.area_disponivel_m2) < 0 ? 'at-baixa-row--ruptura' : ''}`.trim()}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--at-space-2)' }}>
                    <AlertTriangle size={16} aria-hidden="true" />
                    <div>
                      <strong>
                        Vidro {v.tipo} {v.espessura}mm
                      </strong>
                      <p className="at-field__hint at-num">Mínimo: {formatarAreaM2(v.estoque_minimo_m2)}</p>
                    </div>
                  </div>
                  <strong className="at-num">{formatarAreaM2(v.area_disponivel_m2)}</strong>
                </div>
              ))}

              {alertas.fundos_criticos.map((f) => (
                <div
                  key={`f-${f.id}`}
                  className={`at-baixa-row ${Number(f.area_disponivel_m2) < 0 ? 'at-baixa-row--ruptura' : ''}`.trim()}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--at-space-2)' }}>
                    <AlertTriangle size={16} aria-hidden="true" />
                    <div>
                      <strong>
                        Fundo {f.tipo} {f.espessura}mm
                      </strong>
                      <p className="at-field__hint at-num">Mínimo: {formatarAreaM2(f.estoque_minimo_m2)}</p>
                    </div>
                  </div>
                  <strong className="at-num">{formatarAreaM2(f.area_disponivel_m2)}</strong>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
