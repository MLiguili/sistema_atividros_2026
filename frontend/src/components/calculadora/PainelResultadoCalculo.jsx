import React from 'react';
import { Calculator, RefreshCw, ShoppingCart } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import EmptyState from '../ui/EmptyState';
import { formatarAreaM2, formatarMetragem, formatarMoeda } from '../../utils/formatadores';

/**
 * Painel de exibição do cálculo dimensional, áreas e composição de custos sugeridos.
 *
 * @param {{
 *   resultado: object | null,
 *   quantidade: number,
 *   onLimpar: () => void,
 *   onAdicionarAoPedido?: () => void,
 *   textoBotaoAdicionar?: string
 * }} props Propriedades do painel.
 * @returns {JSX.Element} Painel de resultado.
 */
const PainelResultadoCalculo = ({
  resultado,
  quantidade,
  onLimpar,
  onAdicionarAoPedido,
  textoBotaoAdicionar = 'Adicionar ao Pedido',
}) => {
  if (!resultado) {
    return (
      <Card>
        <EmptyState
          icon={<Calculator size={40} aria-hidden="true" />}
          title="Pronto para calcular"
          description="Preencha medidas e materiais ao lado para gerar o orçamento determinístico."
        />
      </Card>
    );
  }

  const qtdNum = Math.max(1, Number(quantidade || 1));

  return (
    <Card>
      <div className="at-calc-result-total">
        <p className="at-muted">Total Sugerido ({qtdNum} {qtdNum === 1 ? 'unidade' : 'unidades'})</p>
        <p className="at-calc-result-total__valor at-num">{formatarMoeda(resultado.total_sugerido)}</p>
        <p className="at-secondary at-num">
          Unitário sugerido: {formatarMoeda(resultado.valor_sugerido_unitario)}
        </p>
      </div>

      <h3 style={{ marginBottom: 'var(--at-space-2)' }}>Dimensões Propagadas</h3>
      <div className="at-calc-list" style={{ marginBottom: 'var(--at-space-4)' }}>
        <div className="at-calc-list__row">
          <span className="at-muted">Obra:</span>
          <span className="at-num">
            {resultado.dimensoes.obra.largura} × {resultado.dimensoes.obra.altura} cm
          </span>
        </div>
        <div className="at-calc-list__row">
          <span className="at-muted">Vidro / Fundo:</span>
          <span className="at-num">
            {resultado.dimensoes.vidro.largura} × {resultado.dimensoes.vidro.altura} cm ({formatarAreaM2(resultado.areas.area_real_m2)})
          </span>
        </div>
        {Number(resultado.areas.area_cobrada_vidro_m2) > Number(resultado.areas.area_real_m2) && (
          <div className="at-calc-list__row">
            <span className="at-muted">Área mínima cobrada (vidro):</span>
            <span className="at-num">{formatarAreaM2(resultado.areas.area_cobrada_vidro_m2)}</span>
          </div>
        )}
        {resultado.dimensoes.molduras.map((m, i) => (
          <div key={i} className="at-calc-list__row">
            <span className="at-muted">
              Moldura {i + 1} ({m.codigo}):
            </span>
            <span className="at-num">
              {m.largura} × {m.altura} cm · {formatarMetragem(m.metragem_total_m)} ({m.barras_sugeridas} bar.)
            </span>
          </div>
        ))}
        <div className="at-calc-list__row at-calc-list__row--total">
          <span>Quadro Final:</span>
          <span className="at-num" style={{ color: 'var(--at-color-text-brand)' }}>
            {resultado.dimensoes.quadro_final.largura} × {resultado.dimensoes.quadro_final.altura} cm
          </span>
        </div>
      </div>

      <h3 style={{ marginBottom: 'var(--at-space-2)' }}>Composição de Custos Unitários</h3>
      <div className="at-calc-list" style={{ marginBottom: 'var(--at-space-4)' }}>
        {resultado.custos.map((c, idx) => (
          <div key={idx} className="at-calc-list__row">
            <span className="at-secondary">
              {c.nome}{' '}
              <span className="at-muted at-num">
                ({c.medida} {c.unidade})
              </span>
            </span>
            <strong className="at-num">{formatarMoeda(c.subtotal)}</strong>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-2)' }}>
        {onAdicionarAoPedido && (
          <Button variant="primary" onClick={onAdicionarAoPedido}>
            <ShoppingCart size={18} aria-hidden="true" />
            <span>{textoBotaoAdicionar}</span>
          </Button>
        )}
        <Button variant="secondary" onClick={onLimpar}>
          <RefreshCw size={16} aria-hidden="true" />
          <span>Limpar Simulação</span>
        </Button>
      </div>
    </Card>
  );
};

export default PainelResultadoCalculo;
