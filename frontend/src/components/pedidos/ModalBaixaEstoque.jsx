import React, { useEffect, useState } from 'react';
import { Hammer } from 'lucide-react';
import api from '../../api/config';
import Dialog from '../ui/Dialog';
import Button from '../ui/Button';
import Field from '../ui/Field';
import Callout from '../ui/Callout';
import { formatarAreaM2 } from '../../utils/formatadores';

/**
 * Modal de Baixa Assistida de Estoque ao iniciar a produção de um pedido (DD-007).
 * Permite ajuste manual de barras via steppers >= 44px e não bloqueia ruptura de estoque.
 *
 * @param {{
 *   open: boolean,
 *   onClose: () => void,
 *   pedido: object | null,
 *   onConfirmado: (respostaBaixa: object) => void
 * }} props Propriedades do modal de baixa.
 * @returns {JSX.Element | null} Modal de Baixa Assistida.
 */
const ModalBaixaEstoque = ({ open, onClose, pedido, onConfirmado }) => {
  const [previsao, setPrevisao] = useState(null);
  const [ajustesMolduras, setAjustesMolduras] = useState({});
  const [observacao, setObservacao] = useState('');
  const [carregando, setCarregando] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState('');

  useEffect(() => {
    if (!open || !pedido) return;
    const carregarPrevisao = async () => {
      setCarregando(true);
      setErro('');
      setObservacao('');
      try {
        const resp = await api.get(`/pedidos/${pedido.id}/previsao-baixa`);
        setPrevisao(resp.data);
        const mapa = {};
        (resp.data.molduras || []).forEach((m) => {
          mapa[m.moldura_id] = m.barras_sugeridas;
        });
        setAjustesMolduras(mapa);
      } catch (err) {
        setErro(err.response?.data?.detail || 'Erro ao carregar previsão de baixa de estoque.');
      } finally {
        setCarregando(false);
      }
    };
    carregarPrevisao();
  }, [open, pedido]);

  if (!pedido) return null;

  const atualizarBarras = (molduraId, valor) => {
    const inteiro = Math.max(0, parseInt(String(valor || 0), 10) || 0);
    setAjustesMolduras((atual) => ({ ...atual, [molduraId]: inteiro }));
  };

  const moldurasComProjecao = (previsao?.molduras || []).map((m) => {
    const baixar = ajustesMolduras[m.moldura_id] ?? m.barras_sugeridas;
    const saldoProj = Number(m.estoque_atual_barras) - baixar;
    return { ...m, barras_baixar: baixar, saldo_projetado_live: saldoProj, em_ruptura_live: saldoProj < 0 };
  });

  const haRuptura =
    moldurasComProjecao.some((m) => m.em_ruptura_live) ||
    (previsao?.vidros || []).some((v) => v.em_ruptura) ||
    (previsao?.fundos || []).some((f) => f.em_ruptura);

  const confirmarBaixa = async () => {
    setEnviando(true);
    setErro('');
    try {
      const payload = {
        ajustes_molduras: moldurasComProjecao.map((m) => ({
          moldura_id: m.moldura_id,
          barras_baixadas: m.barras_baixar,
        })),
        observacao: observacao.trim() || null,
      };
      const resp = await api.post(`/pedidos/${pedido.id}/baixa-estoque`, payload);
      onConfirmado(resp.data);
      onClose();
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao confirmar baixa de estoque.');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={`Baixa Assistida — ${pedido.numero_pedido}`}
      size="lg"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={onClose} disabled={enviando}>
            Cancelar
          </Button>
          <Button
            type="button"
            variant="primary"
            onClick={confirmarBaixa}
            loading={enviando}
            disabled={carregando}
          >
            <Hammer size={16} aria-hidden="true" /> Confirmar Baixa e Iniciar Produção
          </Button>
        </>
      }
    >
      {erro && <Callout variant="danger">{erro}</Callout>}

      {carregando || !previsao ? (
        <p className="at-muted">Calculando consumo previsto de materiais...</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-4)' }}>
          {!previsao.possui_insumos_estoque && (
            <Callout variant="info">
              Este pedido não possui insumos vinculados ao estoque físico. Confirmar apenas moverá o pedido para Em Produção.
            </Callout>
          )}

          {haRuptura && (
            <Callout variant="warning">
              <strong>Atenção — Ruptura de Estoque Projetada:</strong> Um ou mais materiais ficarão com saldo negativo. Você ainda pode confirmar para não travar a oficina e regularizar a compra depois.
            </Callout>
          )}

          {moldurasComProjecao.length > 0 && (
            <section>
              <h3 style={{ marginBottom: 'var(--at-space-2)' }}>Molduras (por barra)</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-2)' }}>
                {moldurasComProjecao.map((m) => (
                  <div
                    key={m.moldura_id}
                    className={`at-baixa-row ${m.em_ruptura_live ? 'at-baixa-row--ruptura' : ''}`}
                  >
                    <div>
                      <strong>
                        {m.codigo} — {m.cor}
                      </strong>
                      <div className="at-muted at-num" style={{ fontSize: 'var(--at-text-xs)' }}>
                        Sugerido: {m.barras_sugeridas} bar. · Atual: {m.estoque_atual_barras} · Saldo pós-baixa:{' '}
                        <strong>{m.saldo_projetado_live} bar.</strong>
                      </div>
                    </div>

                    <div className="at-stepper">
                      <button
                        type="button"
                        className="at-stepper__btn"
                        aria-label={`Diminuir barras de ${m.codigo}`}
                        onClick={() => atualizarBarras(m.moldura_id, m.barras_baixar - 1)}
                      >
                        −
                      </button>
                      <input
                        type="number"
                        min="0"
                        className="at-input at-stepper__input at-num"
                        aria-label={`Quantidade de barras para ${m.codigo}`}
                        value={m.barras_baixar}
                        onChange={(e) => atualizarBarras(m.moldura_id, e.target.value)}
                      />
                      <button
                        type="button"
                        className="at-stepper__btn"
                        aria-label={`Aumentar barras de ${m.codigo}`}
                        onClick={() => atualizarBarras(m.moldura_id, m.barras_baixar + 1)}
                      >
                        +
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {previsao.vidros?.length > 0 && (
            <section>
              <h3 style={{ marginBottom: 'var(--at-space-2)' }}>Vidros (área real em m²)</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-2)' }}>
                {previsao.vidros.map((v) => (
                  <div key={v.id} className={`at-baixa-row ${v.em_ruptura ? 'at-baixa-row--ruptura' : ''}`}>
                    <div>
                      <strong>{v.descricao}</strong>
                      <div className="at-muted at-num" style={{ fontSize: 'var(--at-text-xs)' }}>
                        Baixar: {formatarAreaM2(v.area_a_baixar_m2)} · Disponível: {formatarAreaM2(v.area_disponivel_m2)}
                      </div>
                    </div>
                    <strong className="at-num">Saldo pós-baixa: {formatarAreaM2(v.saldo_projetado_m2)}</strong>
                  </div>
                ))}
              </div>
            </section>
          )}

          {previsao.fundos?.length > 0 && (
            <section>
              <h3 style={{ marginBottom: 'var(--at-space-2)' }}>Fundos (área real em m²)</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-2)' }}>
                {previsao.fundos.map((f) => (
                  <div key={f.id} className={`at-baixa-row ${f.em_ruptura ? 'at-baixa-row--ruptura' : ''}`}>
                    <div>
                      <strong>{f.descricao}</strong>
                      <div className="at-muted at-num" style={{ fontSize: 'var(--at-text-xs)' }}>
                        Baixar: {formatarAreaM2(f.area_a_baixar_m2)} · Disponível: {formatarAreaM2(f.area_disponivel_m2)}
                      </div>
                    </div>
                    <strong className="at-num">Saldo pós-baixa: {formatarAreaM2(f.saldo_projetado_m2)}</strong>
                  </div>
                ))}
              </div>
            </section>
          )}

          <Field id="baixa-obs" label="Observação da Oficina (opcional)">
            <input
              id="baixa-obs"
              className="at-input"
              placeholder="Ex.: Aproveitamento de sobra da prateleira B"
              value={observacao}
              onChange={(e) => setObservacao(e.target.value)}
            />
          </Field>
        </div>
      )}
    </Dialog>
  );
};

export default ModalBaixaEstoque;
