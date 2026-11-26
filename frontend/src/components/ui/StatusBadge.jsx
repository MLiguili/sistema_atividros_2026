import React from 'react';
import {
  Archive,
  BadgeCheck,
  Ban,
  Box,
  CheckCircle2,
  CircleDollarSign,
  Clock,
  Coins,
  FileEdit,
  Hammer,
  ListOrdered,
  PackageCheck,
  PackageSearch,
  RotateCcw,
  Sparkles,
} from 'lucide-react';

const MAPA_STATUS = {
  geral: {
    rascunho: { label: 'Orçamento (Rascunho)', Icon: FileEdit },
    confirmado: { label: 'Confirmado', Icon: CheckCircle2 },
    entregue: { label: 'Entregue', Icon: PackageCheck },
    arquivado: { label: 'Arquivado', Icon: Archive },
    cancelado: { label: 'Cancelado', Icon: Ban },
  },
  producao: {
    pendente: { label: 'Pendente', Icon: Clock },
    aguardando_material: { label: 'Aguard. Material', Icon: PackageSearch },
    na_fila: { label: 'Na Fila', Icon: ListOrdered },
    em_producao: { label: 'Em Produção', Icon: Hammer },
    embalando: { label: 'Embalando', Icon: Box },
    pronto_entrega: { label: 'Pronto p/ Entrega', Icon: Sparkles },
  },
  financeiro: {
    sem_pagamento: { label: 'Sem Pagamento', Icon: CircleDollarSign },
    pagamento_parcial: { label: 'Pgto. Parcial', Icon: Coins },
    pago_total: { label: 'Pago Total', Icon: BadgeCheck },
    estornado: { label: 'Estornado', Icon: RotateCcw },
  },
};

/**
 * Badge acessível dos 3 eixos de status do pedido combinando cor semântica, ícone e traço de borda (DD-005).
 *
 * @param {{
 *   eixo: 'geral' | 'producao' | 'financeiro',
 *   status: string,
 *   extraText?: string
 * }} props Propriedades do badge.
 * @returns {JSX.Element} Badge de status.
 */
const StatusBadge = ({ eixo, status, extraText = '' }) => {
  const cfg = MAPA_STATUS[eixo]?.[status] || { label: status, Icon: Clock };
  const { label, Icon } = cfg;

  return (
    <span className={`at-status at-status--${eixo}-${status}`}>
      <Icon size={13} aria-hidden="true" />
      <span>
        {label}
        {extraText ? ` · ${extraText}` : ''}
      </span>
    </span>
  );
};

export default StatusBadge;
