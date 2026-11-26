from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.models.pedido import (
    Eixo,
    FormaPagamento,
    StatusFinanceiro,
    StatusGeral,
    StatusProducao,
    TipoDesconto,
    TipoItemPedido,
)
from app.schemas.cliente import RespostaCliente


class ItemPedidoMolduraInput(BaseModel):
    """
    Referência ordenada de moldura enviada ao criar/editar um item de pedido.
    """

    moldura_id: int
    ordem: int = Field(default=0, ge=0)


class RespostaItemPedidoMoldura(BaseModel):
    """
    Snapshot persistido de cada moldura aplicada a um item de pedido.
    """

    id: int
    moldura_id: int
    ordem: int
    codigo_moldura_snapshot: str
    largura_barra_cm: Decimal
    tamanho_barra_m: Decimal
    preco_m_aplicado: Decimal
    altura_calculada_cm: Decimal
    largura_calculada_cm: Decimal
    metragem_total_m: Decimal
    barras_sugeridas: int
    model_config = ConfigDict(from_attributes=True)


class CriarItemPedido(BaseModel):
    """
    Payload de criação ou atualização de item em um pedido (quadro, vidro avulso ou serviço livre).
    """

    tipo_item: TipoItemPedido = TipoItemPedido.quadro_sob_medida
    descricao: str | None = Field(default=None, max_length=500)
    quantidade: int = Field(default=1, ge=1)
    preco_unitario: Decimal | None = Field(default=None, ge=0)

    obra_largura: Decimal | None = Field(default=None, gt=0)
    obra_altura: Decimal | None = Field(default=None, gt=0)
    paspatour: bool = False
    tamanho_paspatour: Decimal = Field(default=Decimal("0.00"), ge=0)
    paspatour_id: int | None = None
    vidro_tipo: str | None = None
    vidro_id: int | None = None
    fundo_tipo: str | None = None
    fundo_id: int | None = None
    mao_de_obra: Decimal = Field(default=Decimal("0.00"), ge=0)
    molduras: list[ItemPedidoMolduraInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validar_por_tipo_item(self) -> "CriarItemPedido":
        """
        Valida campos obrigatórios de acordo com o tipo do item.
        """
        if self.tipo_item == TipoItemPedido.servico_livre:
            if not self.descricao or not self.descricao.strip():
                raise ValueError("Descrição é obrigatória para itens do tipo servico_livre")
            if self.preco_unitario is None:
                raise ValueError("preco_unitario é obrigatório para itens do tipo servico_livre")
        else:
            if self.obra_largura is None or self.obra_altura is None:
                raise ValueError("obra_largura e obra_altura são obrigatórios para itens sob medida")
            if self.tipo_item == TipoItemPedido.vidro_avulso and not (self.vidro_tipo or self.vidro_id):
                raise ValueError("vidro_tipo ou vidro_id é obrigatório para vidro_avulso")
        return self


class RespostaItemPedido(BaseModel):
    """
    Representação completa de item persistido no pedido com composição e alerta interno de preço.
    """

    id: int
    tipo_item: TipoItemPedido
    descricao: str
    quantidade: int
    valor_sugerido: Decimal
    preco_unitario: Decimal
    subtotal: Decimal
    obra_largura: Decimal | None = None
    obra_altura: Decimal | None = None
    paspatour: bool
    tamanho_paspatour: Decimal
    paspatour_id: int | None = None
    vidro_id: int | None = None
    vidro_tipo: str | None = None
    fundo_id: int | None = None
    fundo_tipo: str | None = None
    mao_de_obra: Decimal
    snapshot_calculo: dict | None = None
    molduras: list[RespostaItemPedidoMoldura] = []
    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def abaixo_do_sugerido(self) -> bool:
        """
        Indica se o preço unitário praticado ficou abaixo do sugerido pelo motor de cálculo.
        """
        return Decimal(str(self.preco_unitario)) < Decimal(str(self.valor_sugerido))


class CriarPedido(BaseModel):
    """
    Payload para criação ou atualização completa de pedido em rascunho.
    """

    cliente_id: int
    data_validade_orcamento: date | None = None
    prazo_entrega: date | None = None
    endereco_entrega: str | None = Field(default=None, max_length=255)
    frete: Decimal = Field(default=Decimal("0.00"), ge=0)
    desconto_valor: Decimal = Field(default=Decimal("0.00"), ge=0)
    desconto_tipo: TipoDesconto = TipoDesconto.valor
    observacoes: str | None = None
    itens: list[CriarItemPedido] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validar_desconto(self) -> "CriarPedido":
        """
        Impede desconto percentual acima de 100%.
        """
        if self.desconto_tipo == TipoDesconto.percentual and self.desconto_valor > Decimal("100"):
            raise ValueError("Desconto percentual não pode exceder 100%")
        return self


class AtualizarStatusPedido(BaseModel):
    """
    Payload para transição de status nos eixos geral ou produção.
    """

    eixo: Eixo
    novo_status: str
    observacao: str | None = None


class CriarPagamentoPedido(BaseModel):
    """
    Payload para registro de lançamento financeiro (sinal, parcela ou quitação).
    """

    valor: Decimal = Field(..., gt=0)
    forma_pagamento: FormaPagamento
    data_pagamento: datetime | None = None
    observacao: str | None = Field(default=None, max_length=255)


class EstornarPagamentoPedido(BaseModel):
    """
    Payload opcional com motivo para estorno de pagamento.
    """

    motivo: str | None = Field(default=None, max_length=255)


class RespostaPagamentoPedido(BaseModel):
    """
    Representação de lançamento financeiro vinculado a um pedido.
    """

    id: int
    pedido_id: int
    valor: Decimal
    forma_pagamento: FormaPagamento
    data_pagamento: datetime
    observacao: str | None = None
    estornado: bool
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class RespostaEventoPedido(BaseModel):
    """
    Representação cronológica de um evento de auditoria do pedido.
    """

    id: int
    eixo: Eixo
    status_anterior: str | None = None
    status_novo: str
    observacao: str | None = None
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class AjusteMolduraBaixa(BaseModel):
    """
    Ajuste manual de barras de moldura informado pelo operador na Baixa Assistida.
    """

    moldura_id: int
    barras_baixadas: int = Field(..., ge=0)


class ConfirmarBaixaEstoque(BaseModel):
    """
    Payload de confirmação da Baixa Assistida e transição para em_producao.
    """

    ajustes_molduras: list[AjusteMolduraBaixa] = Field(default_factory=list)
    observacao: str | None = Field(default=None, max_length=255)


class PrevisaoMoldura(BaseModel):
    """
    Previsão de consumo e projeção de saldo para uma moldura na Baixa Assistida.
    """

    moldura_id: int
    codigo: str
    cor: str
    barras_sugeridas: int
    estoque_atual_barras: int
    saldo_projetado: int
    em_ruptura: bool


class PrevisaoArea(BaseModel):
    """
    Previsão de consumo em m² reais para vidro ou fundo na Baixa Assistida.
    """

    id: int
    descricao: str
    area_a_baixar_m2: Decimal
    area_disponivel_m2: Decimal
    saldo_projetado_m2: Decimal
    em_ruptura: bool


class RespostaPrevisaoBaixa(BaseModel):
    """
    Estrutura de pré-visualização da Baixa Assistida exibida antes de iniciar a produção.
    """

    possui_insumos_estoque: bool
    molduras: list[PrevisaoMoldura]
    vidros: list[PrevisaoArea]
    fundos: list[PrevisaoArea]


class MaterialBaixado(BaseModel):
    """
    Detalhe de cada material debitado do estoque na confirmação da Baixa Assistida.
    """

    tipo: str
    id: int
    descricao: str
    consumo: Decimal
    unidade: str
    saldo_atual: Decimal
    em_ruptura: bool


class RespostaPedido(BaseModel):
    """
    Representação completa do pedido com itens, molduras, pagamentos, eventos e cliente.
    """

    id: int
    cliente_id: int
    numero_pedido: str
    status_geral: StatusGeral
    status_producao: StatusProducao
    status_financeiro: StatusFinanceiro
    data_validade_orcamento: date | None = None
    prazo_entrega: date | None = None
    endereco_entrega: str | None = None
    frete: Decimal
    desconto_valor: Decimal
    desconto_tipo: TipoDesconto
    subtotal_itens: Decimal
    valor_total: Decimal
    valor_pago: Decimal
    saldo_devedor: Decimal
    observacoes: str | None = None
    criado_em: datetime
    atualizado_em: datetime
    cliente: RespostaCliente | None = None
    itens: list[RespostaItemPedido] = []
    pagamentos: list[RespostaPagamentoPedido] = []
    eventos: list[RespostaEventoPedido] = []
    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def requer_estorno(self) -> bool:
        """
        Indica pedido cancelado que ainda possui saldo pago não estornado.
        """
        return self.status_geral == StatusGeral.cancelado and Decimal(str(self.valor_pago)) > Decimal("0.00")

    @computed_field
    @property
    def tem_item_abaixo_do_sugerido(self) -> bool:
        """
        Indica se ao menos um item do pedido está com preço praticado abaixo do sugerido.
        """
        return any(item.abaixo_do_sugerido for item in self.itens)


class RespostaBaixaEstoque(BaseModel):
    """
    Retorno completo da operação de Baixa Assistida com rupturas eventuais.
    """

    pedido: RespostaPedido
    materiais_baixados: list[MaterialBaixado]
    alertas_ruptura: list[str]


class RespostaPedidoResumo(BaseModel):
    """
    Resumo enxuto de pedido utilizado no histórico por cliente.
    """

    id: int
    cliente_id: int
    numero_pedido: str
    status_geral: StatusGeral
    status_producao: StatusProducao
    status_financeiro: StatusFinanceiro
    data_validade_orcamento: date | None = None
    prazo_entrega: date | None = None
    valor_total: Decimal
    valor_pago: Decimal
    saldo_devedor: Decimal
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)
