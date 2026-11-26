import React, { useEffect, useState } from 'react';
import { CircleDollarSign, RotateCcw } from 'lucide-react';
import api from '../../api/config';
import Dialog from '../ui/Dialog';
import Button from '../ui/Button';
import Field from '../ui/Field';
import Callout from '../ui/Callout';
import { formatarData, formatarMoeda } from '../../utils/formatadores';

const FORMAS_PAGAMENTO = [
  { value: 'pix', label: 'PIX' },
  { value: 'cartao_credito', label: 'Cartão de Crédito' },
  { value: 'cartao_debito', label: 'Cartão de Débito' },
  { value: 'dinheiro', label: 'Dinheiro' },
  { value: 'outro', label: 'Outro' },
];

/**
 * Modal de gestão financeira do pedido (lançamento de pagamentos parciais/totais e estornos).
 *
 * @param {{
 *   open: boolean,
 *   onClose: () => void,
 *   pedido: object | null,
 *   onAtualizado: (pedidoAtualizado: object) => void
 * }} props Propriedades do modal de pagamentos.
 * @returns {JSX.Element | null} Modal financeiro do pedido.
 */
const ModalPagamento = ({ open, onClose, pedido, onAtualizado }) => {
  const [valor, setValor] = useState('');
  const [forma, setForma] = useState('pix');
  const [observacao, setObservacao] = useState('');
  const [erro, setErro] = useState('');
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    if (!open || !pedido) return;
    setErro('');
    setObservacao('');
    const devedor = Number(pedido.saldo_devedor || 0);
    setValor(devedor > 0 ? devedor.toFixed(2) : '');
    setForma('pix');
  }, [open, pedido]);

  if (!pedido) return null;

  const registrarPagamento = async (e) => {
    e.preventDefault();
    setErro('');
    const num = Number(valor);
    if (!num || num <= 0) {
      setErro('Informe um valor de pagamento maior que zero.');
      return;
    }
    setSalvando(true);
    try {
      const resp = await api.post(`/pedidos/${pedido.id}/pagamentos`, {
        valor: num,
        forma_pagamento: forma,
        observacao: observacao.trim() || null,
      });
      onAtualizado(resp.data);
      setObservacao('');
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao registrar pagamento.');
    } finally {
      setSalvando(false);
    }
  };

  const estornarPagamento = async (pagId) => {
    setErro('');
    setSalvando(true);
    try {
      const resp = await api.post(`/pedidos/${pedido.id}/pagamentos/${pagId}/estornar`, {
        motivo: 'Estorno solicitado pelo operador',
      });
      onAtualizado(resp.data);
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao estornar pagamento.');
    } finally {
      setSalvando(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} title={`Pagamentos — ${pedido.numero_pedido}`} size="md">
      {erro && <Callout variant="danger">{erro}</Callout>}

      {pedido.status_geral === 'rascunho' && (
        <Callout variant="info">
          Este pedido ainda é um orçamento em rascunho. Ao registrar o primeiro pagamento, ele será confirmado automaticamente e aparecerá no Kanban de produção.
        </Callout>
      )}

      <div className="at-grid-3" style={{ marginBottom: 'var(--at-space-4)' }}>
        <div className="at-card">
          <div className="at-muted">Total do Pedido</div>
          <strong className="at-num">{formatarMoeda(pedido.valor_total)}</strong>
        </div>
        <div className="at-card">
          <div className="at-muted">Valor Pago</div>
          <strong className="at-num">{formatarMoeda(pedido.valor_pago)}</strong>
        </div>
        <div className="at-card">
          <div className="at-muted">Saldo Devedor</div>
          <strong className="at-num" style={{ color: 'var(--at-color-text-brand)' }}>
            {formatarMoeda(pedido.saldo_devedor)}
          </strong>
        </div>
      </div>

      {pedido.status_geral !== 'cancelado' && Number(pedido.saldo_devedor) > 0 && (
        <form
          onSubmit={registrarPagamento}
          className="at-card"
          style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-3)', marginBottom: 'var(--at-space-4)' }}
        >
          <h3>Novo Recebimento</h3>
          <div className="at-grid-2">
            <Field id="pag-valor" label="Valor (R$)" required>
              <input
                id="pag-valor"
                type="number"
                step="0.01"
                min="0.01"
                required
                className="at-input at-num"
                value={valor}
                onChange={(e) => setValor(e.target.value)}
              />
            </Field>
            <Field id="pag-forma" label="Forma de Pagamento" required>
              <select
                id="pag-forma"
                className="at-select"
                value={forma}
                onChange={(e) => setForma(e.target.value)}
              >
                {FORMAS_PAGAMENTO.map((f) => (
                  <option key={f.value} value={f.value}>
                    {f.label}
                  </option>
                ))}
              </select>
            </Field>
          </div>
          <Field id="pag-obs" label="Observação">
            <input
              id="pag-obs"
              className="at-input"
              placeholder="Ex.: Sinal de 50% via PIX"
              value={observacao}
              onChange={(e) => setObservacao(e.target.value)}
            />
          </Field>
          <div className="at-actions" style={{ justifyContent: 'flex-end' }}>
            <Button type="submit" variant="primary" loading={salvando}>
              <CircleDollarSign size={16} aria-hidden="true" /> Registrar Pagamento
            </Button>
          </div>
        </form>
      )}

      <section>
        <h3 style={{ marginBottom: 'var(--at-space-2)' }}>Lançamentos Registrados</h3>
        {(pedido.pagamentos || []).length === 0 ? (
          <p className="at-muted">Nenhum pagamento registrado até o momento.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-2)' }}>
            {pedido.pagamentos.map((pag) => (
              <div key={pag.id} className="at-baixa-row">
                <div>
                  <strong className="at-num">{formatarMoeda(pag.valor)}</strong>{' '}
                  <span className="at-muted">({pag.forma_pagamento})</span>
                  <div className="at-muted" style={{ fontSize: 'var(--at-text-xs)' }}>
                    {formatarData(pag.data_pagamento)}
                    {pag.estornado ? ' · ESTORNADO' : ''}
                    {pag.observacao ? ` · ${pag.observacao}` : ''}
                  </div>
                </div>
                {!pag.estornado && (
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    disabled={salvando}
                    onClick={() => estornarPagamento(pag.id)}
                  >
                    <RotateCcw size={14} aria-hidden="true" /> Estornar
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </Dialog>
  );
};

export default ModalPagamento;
