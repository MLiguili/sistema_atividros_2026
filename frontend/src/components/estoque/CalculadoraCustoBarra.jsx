import React, { useState } from 'react';
import Button from '../ui/Button';
import Field from '../ui/Field';
import { calcularCustoPorMetroDeBarra, formatarMoeda } from '../../utils/formatadores';

/**
 * Auxiliar expansível no formulário de moldura para converter custo de barra inteira em R$/m (DD-004).
 *
 * @param {{
 *   tamanhoBarra: string | number,
 *   onAplicarCustoMetro: (custoMetro: string) => void
 * }} props Propriedades do auxiliar.
 * @returns {JSX.Element} Bloco expansível de cálculo auxiliar.
 */
const CalculadoraCustoBarra = ({ tamanhoBarra, onAplicarCustoMetro }) => {
  const [aberto, setAberto] = useState(false);
  const [custoBarra, setCustoBarra] = useState('');

  const tamanhoValido = Number(tamanhoBarra) > 0;
  const custoPorMetro = tamanhoValido ? calcularCustoPorMetroDeBarra(custoBarra, tamanhoBarra) : null;

  return (
    <div>
      <Button variant="ghost" size="sm" onClick={() => setAberto((v) => !v)}>
        {aberto ? 'Ocultar auxiliar de custo por barra' : 'Calcular a partir do custo da barra'}
      </Button>

      {aberto && (
        <div className="at-custo-helper">
          {!tamanhoValido ? (
            <p className="at-field__hint">Informe primeiro o Tamanho da Barra (m) acima.</p>
          ) : (
            <>
              <Field id="helper-custo-barra" label={`Custo da barra inteira (R$ para ${tamanhoBarra} m)`}>
                <input
                  id="helper-custo-barra"
                  type="number"
                  step="0.01"
                  min="0"
                  className="at-input at-num"
                  value={custoBarra}
                  onChange={(e) => setCustoBarra(e.target.value)}
                  placeholder="Ex.: 75.00"
                />
              </Field>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 'var(--at-space-2)' }}>
                <span className="at-num at-secondary">
                  {custoPorMetro !== null ? `Equivalente: ${formatarMoeda(custoPorMetro)}/m` : 'Digite o custo da barra'}
                </span>
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={custoPorMetro === null}
                  onClick={() => {
                    if (custoPorMetro !== null) {
                      onAplicarCustoMetro(custoPorMetro.toFixed(2));
                      setAberto(false);
                    }
                  }}
                >
                  Aplicar ao custo/m
                </Button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default CalculadoraCustoBarra;
