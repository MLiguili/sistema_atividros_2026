/**
 * Formata um valor numérico como moeda brasileira (R$ X.XXX,XX).
 *
 * @param {number | string | null | undefined} valor Valor monetário.
 * @returns {string} Valor formatado em pt-BR.
 */
export const formatarMoeda = (valor) => {
  const num = Number(valor || 0);
  if (Number.isNaN(num)) return 'R$ 0,00';
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
};

/**
 * Formata uma medida linear em centímetros com 2 casas decimais.
 *
 * @param {number | string | null | undefined} cm Valor em centímetros.
 * @returns {string} Medida formatada.
 */
export const formatarMedidaCm = (cm) => {
  const num = Number(cm || 0);
  if (Number.isNaN(num)) return '0,00 cm';
  return `${num.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} cm`;
};

/**
 * Formata uma área em metros quadrados (m²) com 4 casas decimais.
 *
 * @param {number | string | null | undefined} m2 Área em m².
 * @returns {string} Área formatada.
 */
export const formatarAreaM2 = (m2) => {
  const num = Number(m2 || 0);
  if (Number.isNaN(num)) return '0,0000 m²';
  return `${num.toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 })} m²`;
};

/**
 * Formata metragem linear em metros com 2 ou 4 casas decimais.
 *
 * @param {number | string | null | undefined} metros Metragem em metros.
 * @returns {string} Metragem formatada.
 */
export const formatarMetragem = (metros) => {
  const num = Number(metros || 0);
  if (Number.isNaN(num)) return '0,00 m';
  return `${num.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 4 })} m`;
};

/**
 * Formata data ISO ou string YYYY-MM-DD para DD/MM/AAAA em pt-BR.
 *
 * @param {string | null | undefined} dataStr String de data/datetime.
 * @returns {string} Data formatada ou traço.
 */
export const formatarData = (dataStr) => {
  if (!dataStr) return '—';
  const apenasData = /^\d{4}-\d{2}-\d{2}$/.test(dataStr);
  const dt = apenasData ? new Date(`${dataStr}T12:00:00`) : new Date(dataStr);
  if (Number.isNaN(dt.getTime())) return '—';
  return dt.toLocaleDateString('pt-BR');
};

/**
 * Calcula o custo por metro linear (R$/m) a partir do custo da barra inteira e seu comprimento.
 *
 * @param {number | string} custoBarra Valor pago pela barra inteira (R$).
 * @param {number | string} tamanhoBarra Comprimento da barra em metros.
 * @returns {number | null} Custo em R$/m arredondado em 2 casas ou null se inválido.
 */
export const calcularCustoPorMetroDeBarra = (custoBarra, tamanhoBarra) => {
  const custo = Number(custoBarra);
  const tamanho = Number(tamanhoBarra);
  if (!Number.isFinite(custo) || !Number.isFinite(tamanho) || tamanho <= 0 || custo < 0) {
    return null;
  }
  return Math.round((custo / tamanho) * 100) / 100;
};

/**
 * Calcula preview local de totais de um pedido (apenas informativo; fonte oficial é o backend).
 *
 * @param {Array<{ preco_unitario?: number | string, quantidade?: number | string }>} itens Lista de itens.
 * @param {number | string} frete Valor do frete.
 * @param {number | string} descontoValor Valor ou percentual do desconto.
 * @param {'valor' | 'percentual'} descontoTipo Modalidade do desconto.
 * @returns {{ subtotalItens: number, descontoCalculado: number, valorTotal: number }} Totais estimados.
 */
export const calcularTotaisPreviewPedido = (itens = [], frete = 0, descontoValor = 0, descontoTipo = 'valor') => {
  const subtotalItens = itens.reduce((acc, item) => {
    const unit = Number(item.preco_unitario || 0);
    const qtd = Number(item.quantidade || 1);
    return acc + unit * qtd;
  }, 0);

  const freteNum = Math.max(0, Number(frete || 0));
  const descIn = Math.max(0, Number(descontoValor || 0));
  const descontoCalculado =
    descontoTipo === 'percentual' ? Math.round((subtotalItens * descIn) ) / 100 : descIn;
  const valorTotal = Math.max(0, Math.round((subtotalItens + freteNum - descontoCalculado) * 100) / 100);

  return {
    subtotalItens: Math.round(subtotalItens * 100) / 100,
    descontoCalculado: Math.round(descontoCalculado * 100) / 100,
    valorTotal,
  };
};

/**
 * Localiza automaticamente a chapa física em estoque associada a um tipo de vidro ou fundo.
 *
 * @param {Array<{ id: number, tipo: string, espessura?: number | string, area_disponivel_m2?: number | string }>} listaEstoque Lista de vidros ou fundos do estoque.
 * @param {string | null | undefined} tipoSelecionado Tipo selecionado na tabela de preços.
 * @returns {object | null} Chapa correspondente prioritariamente com maior saldo em m², ou null se ausente.
 */
export const resolverEstoquePorTipo = (listaEstoque = [], tipoSelecionado = '') => {
  const tipoNorm = String(tipoSelecionado || '').trim().toLowerCase();
  if (!tipoNorm) return null;

  const correspondentes = (listaEstoque || []).filter(
    (item) => String(item.tipo || '').trim().toLowerCase() === tipoNorm,
  );
  if (correspondentes.length === 0) return null;

  return [...correspondentes].sort(
    (a, b) => Number(b.area_disponivel_m2 || 0) - Number(a.area_disponivel_m2 || 0),
  )[0];
};

/**
 * Gera texto orientativo de estoque e necessidade de compra para vidro ou fundo selecionado.
 *
 * @param {Array<object>} listaEstoque Lista de vidros ou fundos do estoque.
 * @param {string | null | undefined} tipoSelecionado Tipo escolhido.
 * @returns {string} Dica contextual de baixa ou compra.
 */
export const descreverDisponibilidadeMaterial = (listaEstoque = [], tipoSelecionado = '') => {
  if (!tipoSelecionado) return 'Nenhum material selecionado.';
  const chapa = resolverEstoquePorTipo(listaEstoque, tipoSelecionado);
  if (!chapa) {
    return 'Material não cadastrado no estoque — precisa ser comprado ao produzir.';
  }
  const saldo = Number(chapa.area_disponivel_m2 || 0);
  if (saldo <= 0) {
    return `Estoque zerado/negativo (${formatarAreaM2(saldo)}) — precisa ser comprado.`;
  }
  return `Baixa automática no estoque: ${chapa.tipo} ${chapa.espessura}mm (${formatarAreaM2(saldo)} disponíveis).`;
};
