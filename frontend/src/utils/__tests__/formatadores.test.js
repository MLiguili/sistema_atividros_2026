import { describe, expect, it } from 'vitest';
import {
  calcularCustoPorMetroDeBarra,
  calcularTotaisPreviewPedido,
  formatarAreaM2,
  formatarData,
  formatarMedidaCm,
  formatarMoeda,
} from '../formatadores';

describe('formatadores utilitários', () => {
  it('formata valores monetários e medidas no padrão pt-BR', () => {
    expect(formatarMoeda(1234.5)).toContain('1.234,50');
    expect(formatarMedidaCm(50)).toBe('50,00 cm');
    expect(formatarAreaM2(0.45)).toBe('0,4500 m²');
    expect(formatarData('2026-11-26')).toBe('26/11/2026');
    expect(formatarData(null)).toBe('—');
  });

  it('calcula custo por metro de barra com precisão e protege divisões inválidas', () => {
    expect(calcularCustoPorMetroDeBarra(55, 2.75)).toBe(20);
    expect(calcularCustoPorMetroDeBarra(30, 0)).toBeNull();
  });

  it('calcula preview de pedido com desconto fixo e percentual + frete', () => {
    const itens = [{ preco_unitario: 100, quantidade: 2 }];
    expect(calcularTotaisPreviewPedido(itens, 25, 10, 'percentual')).toEqual({
      subtotalItens: 200,
      descontoCalculado: 20,
      valorTotal: 205,
    });
    expect(calcularTotaisPreviewPedido(itens, 0, 30, 'valor')).toEqual({
      subtotalItens: 200,
      descontoCalculado: 30,
      valorTotal: 170,
    });
  });
});
