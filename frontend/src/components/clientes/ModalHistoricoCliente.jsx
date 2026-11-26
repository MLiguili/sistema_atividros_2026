import React, { useEffect, useState } from 'react';
import api from '../../api/config';
import Dialog from '../ui/Dialog';
import StatusBadge from '../ui/StatusBadge';
import EmptyState from '../ui/EmptyState';
import Callout from '../ui/Callout';
import { formatarData, formatarMoeda } from '../../utils/formatadores';

/**
 * Modal de histórico de pedidos de um cliente consultado diretamente via endpoint filtrado no servidor.
 *
 * @param {{
 *   cliente: { id: number, nome: string, sobrenome: string } | null,
 *   onClose: () => void
 * }} props Propriedades do modal.
 * @returns {JSX.Element | null} Modal de histórico.
 */
const ModalHistoricoCliente = ({ cliente, onClose }) => {
  const [pedidos, setPedidos] = useState([]);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState('');

  useEffect(() => {
    if (!cliente) return;
    let ativo = true;
    setCarregando(true);
    setErro('');

    api
      .get(`/clientes/${cliente.id}/pedidos`)
      .then((resp) => {
        if (ativo) setPedidos(resp.data || []);
      })
      .catch((err) => {
        if (ativo) setErro(err.response?.data?.detail || 'Erro ao carregar histórico.');
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });

    return () => {
      ativo = false;
    };
  }, [cliente]);

  return (
    <Dialog
      open={Boolean(cliente)}
      onClose={onClose}
      title={cliente ? `Histórico — ${cliente.nome} ${cliente.sobrenome}` : 'Histórico'}
      size="lg"
    >
      {carregando && (
        <div className="at-state" role="status">
          Carregando histórico de pedidos...
        </div>
      )}

      {erro && <Callout variant="danger">{erro}</Callout>}

      {!carregando && !erro && pedidos.length === 0 && (
        <EmptyState
          title="Nenhum pedido registrado"
          description="Este cliente ainda não possui orçamentos ou pedidos vinculados."
        />
      )}

      {!carregando && !erro && pedidos.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-3)' }}>
          {pedidos.map((p) => (
            <div key={p.id} className="at-card at-card--subtle">
              <div className="at-pedido-card__top">
                <div>
                  <strong className="at-num">#{p.numero_pedido}</strong>
                  <span className="at-muted" style={{ marginLeft: 'var(--at-space-2)' }}>
                    Criado em {formatarData(p.criado_em)}
                  </span>
                </div>
                <strong className="at-num">{formatarMoeda(p.valor_total)}</strong>
              </div>
              <div className="at-pedido-card__badges" style={{ marginTop: 'var(--at-space-2)' }}>
                <StatusBadge eixo="geral" status={p.status_geral} />
                <StatusBadge eixo="producao" status={p.status_producao} />
                <StatusBadge eixo="financeiro" status={p.status_financeiro} />
              </div>
            </div>
          ))}
        </div>
      )}
    </Dialog>
  );
};

export default ModalHistoricoCliente;
