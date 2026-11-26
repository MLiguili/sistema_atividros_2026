import React from 'react';
import { Edit3, Eye, FileDown } from 'lucide-react';
import DataTable from '../ui/DataTable';
import StatusBadge from '../ui/StatusBadge';
import Button from '../ui/Button';
import { formatarData, formatarMoeda } from '../../utils/formatadores';

const FILTROS_GERAL = [
  { key: '', label: 'Todos' },
  { key: 'rascunho', label: 'Orçamentos (Rascunho)' },
  { key: 'confirmado', label: 'Confirmados' },
  { key: 'entregue', label: 'Entregues' },
  { key: 'arquivado', label: 'Arquivados' },
  { key: 'cancelado', label: 'Cancelados' },
];

/**
 * Visão tabular de todos os pedidos com filtro por status geral e ações rápidas.
 *
 * @param {{
 *   pedidos: Array<object>,
 *   filtroGeral: string,
 *   onChangeFiltroGeral: (f: string) => void,
 *   onAbrirDetalhe: (p: object) => void,
 *   onEditarRascunho: (p: object) => void,
 *   onBaixarPdf: (p: object) => void
 * }} props Propriedades da lista.
 * @returns {JSX.Element} Lista filtrável de pedidos.
 */
const PedidoLista = ({
  pedidos,
  filtroGeral,
  onChangeFiltroGeral,
  onAbrirDetalhe,
  onEditarRascunho,
  onBaixarPdf,
}) => {
  const filtrados = filtroGeral ? pedidos.filter((p) => p.status_geral === filtroGeral) : pedidos;

  const columns = [
    {
      key: 'numero',
      header: 'Pedido',
      render: (row) => (
        <div>
          <strong className="at-num">{row.numero_pedido}</strong>
          <div className="at-muted" style={{ fontSize: 'var(--at-text-xs)' }}>
            {formatarData(row.criado_em)}
          </div>
        </div>
      ),
    },
    {
      key: 'cliente',
      header: 'Cliente',
      render: (row) => (
        <div>
          <div>{row.cliente?.nome || `Cliente #${row.cliente_id}`}</div>
          {row.prazo_entrega && (
            <div className="at-muted" style={{ fontSize: 'var(--at-text-xs)' }}>
              Prazo: {formatarData(row.prazo_entrega)}
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status (3 Eixos)',
      render: (row) => (
        <div className="at-actions">
          <StatusBadge eixo="geral" status={row.status_geral} />
          <StatusBadge eixo="producao" status={row.status_producao} />
          <StatusBadge eixo="financeiro" status={row.status_financeiro} />
        </div>
      ),
    },
    {
      key: 'valores',
      header: 'Total / Saldo',
      numeric: true,
      render: (row) => (
        <div>
          <strong className="at-num">{formatarMoeda(row.valor_total)}</strong>
          <div className="at-muted at-num" style={{ fontSize: 'var(--at-text-xs)' }}>
            Devedor: {formatarMoeda(row.saldo_devedor)}
          </div>
        </div>
      ),
    },
    {
      key: 'acoes',
      header: 'Ações',
      render: (row) => (
        <div className="at-actions" style={{ justifyContent: 'flex-end' }}>
          <Button variant="ghost" size="sm" onClick={() => onAbrirDetalhe(row)}>
            <Eye size={14} aria-hidden="true" /> Detalhes
          </Button>
          {row.status_geral === 'rascunho' && (
            <Button variant="secondary" size="sm" onClick={() => onEditarRascunho(row)}>
              <Edit3 size={14} aria-hidden="true" /> Editar
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={() => onBaixarPdf(row)} title="Baixar PDF">
            <FileDown size={14} aria-hidden="true" /> PDF
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-3)' }}>
      <div className="at-actions" role="group" aria-label="Filtrar por status do pedido">
        {FILTROS_GERAL.map((f) => (
          <button
            key={f.key || 'todos'}
            type="button"
            className={`at-tab ${filtroGeral === f.key ? 'at-tab--active' : ''}`}
            onClick={() => onChangeFiltroGeral(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      <DataTable
        columns={columns}
        data={filtrados}
        emptyTitle="Nenhum pedido encontrado"
        emptyDescription="Ajuste o filtro ou crie um novo orçamento/pedido."
      />
    </div>
  );
};

export default PedidoLista;
