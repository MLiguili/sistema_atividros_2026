import React, { useEffect, useState } from 'react';
import api from '../../api/config';
import Dialog from '../ui/Dialog';
import Button from '../ui/Button';
import Field from '../ui/Field';
import Callout from '../ui/Callout';
import { formatarAreaM2 } from '../../utils/formatadores';

/**
 * Modal de ajuste manual direto do saldo em m² para inventário de vidros ou fundos.
 *
 * @param {{
 *   categoria: 'vidros' | 'fundos',
 *   item: object | null,
 *   onClose: () => void,
 *   onSuccess: (msg: string) => void
 * }} props Propriedades do modal.
 * @returns {JSX.Element | null} Modal de ajuste manual em m².
 */
const ModalAjusteM2 = ({ categoria, item, onClose, onSuccess }) => {
  const [novaArea, setNovaArea] = useState('');
  const [motivo, setMotivo] = useState('');
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  useEffect(() => {
    if (item) {
      setNovaArea(String(item.area_disponivel_m2 ?? '0.0000'));
      setMotivo('');
      setErro('');
    }
  }, [item]);

  const handleSubmit = async (evento) => {
    evento.preventDefault();
    if (!item) return;
    setErro('');
    setSalvando(true);
    try {
      const resp = await api.post(`/estoque/${categoria}/${item.id}/ajuste-m2`, {
        nova_area_m2: parseFloat(novaArea),
        motivo: motivo.trim() || null,
      });
      onSuccess(`Saldo ajustado para ${formatarAreaM2(resp.data.area_disponivel_m2)}.`);
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao ajustar saldo em m².');
    } finally {
      setSalvando(false);
    }
  };

  return (
    <Dialog
      open={Boolean(item)}
      onClose={onClose}
      title={item ? `Ajuste Manual (m²) — ${item.tipo} (${item.espessura}mm)` : 'Ajuste Manual'}
      size="sm"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={salvando}>
            Cancelar
          </Button>
          <Button type="submit" form="form-ajuste-m2" variant="primary" loading={salvando}>
            Confirmar Ajuste
          </Button>
        </>
      }
    >
      <form id="form-ajuste-m2" onSubmit={handleSubmit}>
        {erro && <Callout variant="danger">{erro}</Callout>}
        <Field id="aj-area" label="Novo Saldo Disponível (m²)" required hint="Permite regularizar saldos negativos">
          <input
            id="aj-area"
            type="number"
            step="0.0001"
            className="at-input at-num"
            value={novaArea}
            onChange={(e) => setNovaArea(e.target.value)}
            required
          />
        </Field>
        <Field id="aj-motivo" label="Motivo (opcional)">
          <input
            id="aj-motivo"
            className="at-input"
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            placeholder="Ex.: Inventário físico ou quebra"
          />
        </Field>
      </form>
    </Dialog>
  );
};

export default ModalAjusteM2;
