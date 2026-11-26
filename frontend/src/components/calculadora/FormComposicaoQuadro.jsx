import React from 'react';
import { Calculator, Plus, Trash2 } from 'lucide-react';
import Card from '../ui/Card';
import Field from '../ui/Field';
import Button from '../ui/Button';

/**
 * Formulário reutilizável de composição técnica para Quadro Sob Medida e Vidro/Espelho Avulso.
 *
 * @param {{
 *   modo: 'quadro_sob_medida' | 'vidro_avulso',
 *   onChangeModo: (m: 'quadro_sob_medida' | 'vidro_avulso') => void,
 *   dados: object,
 *   onChangeDados: (d: object) => void,
 *   catalogos: { molduras: Array, vidros: Array, fundos: Array, tabelaVidro: Array, tabelaFundo: Array, tabelaPaspatour: Array },
 *   onCalcular: () => void,
 *   calculando: boolean
 * }} props Propriedades do formulário.
 * @returns {JSX.Element} Formulário de composição.
 */
const FormComposicaoQuadro = ({
  modo,
  onChangeModo,
  dados,
  onChangeDados,
  catalogos,
  onCalcular,
  calculando,
}) => {
  const adicionarMoldura = () => {
    onChangeDados({
      ...dados,
      molduras: [...dados.molduras, { moldura_id: '', ordem: dados.molduras.length }],
    });
  };

  const removerMoldura = (idx) => {
    const restantes = dados.molduras
      .filter((_, i) => i !== idx)
      .map((m, i) => ({ ...m, ordem: i }));
    onChangeDados({ ...dados, molduras: restantes });
  };

  const atualizarMoldura = (idx, molduraId) => {
    const novas = dados.molduras.map((m, i) => (i === idx ? { ...m, moldura_id: molduraId } : m));
    onChangeDados({ ...dados, molduras: novas });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-4)' }}>
      <Card>
        <div className="at-card__header">
          <h2>Tipo de Item</h2>
          <div className="at-segmented" role="group" aria-label="Tipo de item a calcular">
            <button
              type="button"
              className="at-segmented__btn"
              aria-pressed={modo === 'quadro_sob_medida'}
              onClick={() => onChangeModo('quadro_sob_medida')}
            >
              Quadro Sob Medida
            </button>
            <button
              type="button"
              className="at-segmented__btn"
              aria-pressed={modo === 'vidro_avulso'}
              onClick={() => onChangeModo('vidro_avulso')}
            >
              Vidro / Espelho Avulso
            </button>
          </div>
        </div>

        <div className="at-grid-3">
          <Field id="calc-largura" label={modo === 'vidro_avulso' ? 'Largura (cm)' : 'Largura Obra (cm)'} required>
            <input
              id="calc-largura"
              type="number"
              step="0.01"
              min="0.1"
              className="at-input at-num"
              value={dados.obra_largura}
              onChange={(e) => onChangeDados({ ...dados, obra_largura: e.target.value })}
            />
          </Field>
          <Field id="calc-altura" label={modo === 'vidro_avulso' ? 'Altura (cm)' : 'Altura Obra (cm)'} required>
            <input
              id="calc-altura"
              type="number"
              step="0.01"
              min="0.1"
              className="at-input at-num"
              value={dados.obra_altura}
              onChange={(e) => onChangeDados({ ...dados, obra_altura: e.target.value })}
            />
          </Field>
          <Field id="calc-qtd" label="Quantidade" required>
            <input
              id="calc-qtd"
              type="number"
              min="1"
              step="1"
              className="at-input at-num"
              value={dados.quantidade}
              onChange={(e) => onChangeDados({ ...dados, quantidade: e.target.value })}
            />
          </Field>
        </div>
      </Card>

      {modo === 'quadro_sob_medida' && (
        <>
          <Card>
            <div className="at-card__header">
              <h3>Paspatour</h3>
              <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--at-space-2)', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={dados.paspatour}
                  onChange={(e) => onChangeDados({ ...dados, paspatour: e.target.checked })}
                />
                <span>Usar paspatour</span>
              </label>
            </div>
            {dados.paspatour && (
              <div className="at-grid-2">
                <Field id="calc-pasp-tam" label="Borda (cm)" required>
                  <input
                    id="calc-pasp-tam"
                    type="number"
                    step="0.1"
                    min="0.1"
                    className="at-input at-num"
                    value={dados.tamanho_paspatour}
                    onChange={(e) => onChangeDados({ ...dados, tamanho_paspatour: e.target.value })}
                  />
                </Field>
                <Field id="calc-pasp-id" label="Opção na Tabela de Paspatour" required>
                  <select
                    id="calc-pasp-id"
                    className="at-input"
                    value={dados.paspatour_id}
                    onChange={(e) => onChangeDados({ ...dados, paspatour_id: e.target.value })}
                  >
                    <option value="">Selecione...</option>
                    {catalogos.tabelaPaspatour.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.descricao} (R$ {Number(p.preco_por_m2).toFixed(2)}/m²)
                      </option>
                    ))}
                  </select>
                </Field>
              </div>
            )}
          </Card>

          <Card>
            <div className="at-card__header">
              <h3>Molduras (Interna → Externa)</h3>
              <Button variant="secondary" size="sm" onClick={adicionarMoldura}>
                <Plus size={15} aria-hidden="true" />
                <span>Adicionar Moldura</span>
              </Button>
            </div>

            {dados.molduras.length === 0 ? (
              <p className="at-muted">Nenhuma moldura adicionada (cálculo sem moldura ou adicione acima).</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-2)' }}>
                {dados.molduras.map((m, idx) => (
                  <div key={idx} style={{ display: 'flex', gap: 'var(--at-space-2)', alignItems: 'center' }}>
                    <span className="at-num at-muted" style={{ minWidth: '24px' }}>
                      {idx + 1}.
                    </span>
                    <select
                      aria-label={`Moldura camada ${idx + 1}`}
                      className="at-input"
                      value={m.moldura_id}
                      onChange={(e) => atualizarMoldura(idx, e.target.value)}
                    >
                      <option value="">Selecione a moldura...</option>
                      {catalogos.molduras.map((mol) => (
                        <option key={mol.id} value={mol.id}>
                          {mol.codigo} - {mol.cor} ({mol.largura_barra}cm · R$ {Number(mol.preco_venda).toFixed(2)}/m)
                        </option>
                      ))}
                    </select>
                    <Button
                      variant="icon"
                      onClick={() => removerMoldura(idx)}
                      aria-label={`Remover moldura ${idx + 1}`}
                    >
                      <Trash2 size={16} aria-hidden="true" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </>
      )}

      <Card>
        <h3 style={{ marginBottom: 'var(--at-space-3)' }}>Vidro, Fundo e Mão de Obra</h3>
        <div className="at-grid-2">
          <Field id="calc-vidro-tipo" label="Tabela de Preço — Vidro / Espelho" required={modo === 'vidro_avulso'}>
            <select
              id="calc-vidro-tipo"
              className="at-input"
              value={dados.vidro_tipo}
              onChange={(e) => onChangeDados({ ...dados, vidro_tipo: e.target.value })}
            >
              {modo === 'quadro_sob_medida' && <option value="">Sem vidro</option>}
              {catalogos.tabelaVidro.map((tv) => (
                <option key={tv.id} value={tv.tipo}>
                  {tv.tipo} (R$ {Number(tv.preco_por_m2).toFixed(2)}/m² · mín. {tv.area_minima_m2}m²)
                </option>
              ))}
            </select>
          </Field>

          <Field id="calc-vidro-id" label="Chapa física no Estoque (para baixa)">
            <select
              id="calc-vidro-id"
              className="at-input"
              value={dados.vidro_id}
              onChange={(e) => onChangeDados({ ...dados, vidro_id: e.target.value })}
            >
              <option value="">Sob encomenda / Sem vínculo físico</option>
              {catalogos.vidros.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.tipo} {v.espessura}mm ({Number(v.area_disponivel_m2).toFixed(4)} m²)
                </option>
              ))}
            </select>
          </Field>
        </div>

        {modo === 'quadro_sob_medida' && (
          <div className="at-grid-2">
            <Field id="calc-fundo-tipo" label="Tabela de Preço — Fundo">
              <select
                id="calc-fundo-tipo"
                className="at-input"
                value={dados.fundo_tipo}
                onChange={(e) => onChangeDados({ ...dados, fundo_tipo: e.target.value })}
              >
                <option value="">Sem fundo</option>
                {catalogos.tabelaFundo.map((tf) => (
                  <option key={tf.id} value={tf.tipo}>
                    {tf.tipo} (R$ {Number(tf.preco_por_m2).toFixed(2)}/m²)
                  </option>
                ))}
              </select>
            </Field>

            <Field id="calc-fundo-id" label="Chapa de Fundo no Estoque (para baixa)">
              <select
                id="calc-fundo-id"
                className="at-input"
                value={dados.fundo_id}
                onChange={(e) => onChangeDados({ ...dados, fundo_id: e.target.value })}
              >
                <option value="">Sob encomenda / Sem vínculo físico</option>
                {catalogos.fundos.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.tipo} {f.espessura}mm ({Number(f.area_disponivel_m2).toFixed(4)} m²)
                  </option>
                ))}
              </select>
            </Field>
          </div>
        )}

        <Field
          id="calc-mao-obra"
          label="Mão de obra (R$/un)"
          hint="Somada ao valor unitário de cada quadro/peça"
        >
          <input
            id="calc-mao-obra"
            type="number"
            step="0.01"
            min="0"
            className="at-input at-num"
            value={dados.mao_de_obra}
            onChange={(e) => onChangeDados({ ...dados, mao_de_obra: e.target.value })}
          />
        </Field>
      </Card>

      <Button variant="primary" onClick={onCalcular} loading={calculando}>
        <Calculator size={18} aria-hidden="true" />
        <span>{calculando ? 'Calculando...' : 'Calcular Orçamento'}</span>
      </Button>
    </div>
  );
};

export default FormComposicaoQuadro;
