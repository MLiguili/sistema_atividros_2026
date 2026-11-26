import React, { useState } from 'react';
import api from '../../api/config';
import Dialog from '../ui/Dialog';
import Button from '../ui/Button';
import Field from '../ui/Field';
import Callout from '../ui/Callout';
import { formatarAreaM2 } from '../../utils/formatadores';

/**
 * Modal conversor de entrada de chapas físicas (qtd × largura × altura / 10000) para saldo em m².
 *
 * @param {{
 *   categoria: 'vidros' | 'fundos',
 *   item: object | null,
 *   onClose: () => void,
 *   onSuccess: (msg: string) => void
 * }} props Propriedades do modal.
 * @returns {JSX.Element | null} Modal de entrada de chapas.
 */
const ModalEntradaChapas = ({ categoria, item, onClose, onSuccess }) => {
  const [quantidadeChapas, setQuantidadeChapas] = useState('1');
  const [larguraCm, setLarguraCm] = useState('');
  const [alturaCm, setAlturaCm] = useState('');
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  const previewM2 = (() => {
    const q = Number(quantidadeChapas);
    const l = Number(larguraCm);
    const a = Number(alturaCm);
    if (q >= 1 && l > 0 && a > 0) return (q * l * a) / 10000;
    return 0;
  })();

  const handleSubmit = async (evento) => {
    evento.preventDefault();
    if (!item) return;
    setErro('');
    setSalvando(true);
    try {
      const resp = await api.post(`/estoque/${categoria}/${item.id}/entrada-chapas`, {
        quantidade_chapas: parseInt(quantidadeChapas, 10),
        largura_cm: parseFloat(larguraCm),
        altura_cm: parseFloat(alturaCm),
      });
      onSuccess(`Adicionados ${formatarAreaM2(resp.data.area_adicionada_m2)} ao saldo.`);
      setLarguraCm('');
      setAlturaCm('');
      setQuantidadeChapas('1');
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao registrar entrada de chapas.');
    } finally {
      setSalvando(false);
    }
  };

  return (
    <Dialog
      open={Boolean(item)}
      onClose={onClose}
      title={item ? `Entrada por Chapas — ${item.tipo} (${item.espessura}mm)` : 'Entrada por Chapas'}
      size="sm"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={salvando}>
            Cancelar
          </Button>
          <Button type="submit" form="form-entrada-chapas" variant="primary" loading={salvando}>
            Somar ao Saldo (m²)
          </Button>
        </>
      }
    >
      <form id="form-entrada-chapas" onSubmit={handleSubmit}>
        {erro && <Callout variant="danger">{erro}</Callout>}
        <p className="at-muted" style={{ marginBottom: 'var(--at-space-3)' }}>
          Saldo atual: <strong className="at-num">{formatarAreaM2(item?.area_disponivel_m2)}</strong>
        </p>

        <Field id="ec-qtd" label="Quantidade de Chapas" required>
          <input
            id="ec-qtd"
            type="number"
            min="1"
            step="1"
            className="at-input at-num"
            value={quantidadeChapas}
            onChange={(e) => setQuantidadeChapas(e.target.value)}
            required
          />
        </Field>

        <div className="at-grid-2">
          <Field id="ec-larg" label="Largura da Chapa (cm)" required>
            <input
              id="ec-larg"
              type="number"
              step="0.01"
              min="0.01"
              className="at-input at-num"
              value={larguraCm}
              onChange={(e) => setLarguraCm(e.target.value)}
              placeholder="Ex.: 240"
              required
            />
          </Field>
          <Field id="ec-alt" label="Altura da Chapa (cm)" required>
            <input
              id="ec-alt"
              type="number"
              step="0.01"
              min="0.01"
              className="at-input at-num"
              value={alturaCm}
              onChange={(e) => setAlturaCm(e.target.value)}
              placeholder="Ex.: 180"
              required
            />
          </Field>
        </div>

        <Callout variant="info">
          Área calculada a somar: <strong className="at-num">{formatarAreaM2(previewM2)}</strong>
        </Callout>
      </form>
    </Dialog>
  );
};

export default ModalEntradaChapas;
